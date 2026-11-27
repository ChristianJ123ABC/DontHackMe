#Sources
#OpenRouter API: https://openrouter.ai/docs/api_reference/overview
#https://www.datacamp.com/tutorial/openrouter?dc_referrer=https%3A%2F%2Fwww.google.com%2F
#https://www.youtube.com/watch?v=CHsRy4gl6hk&list=PLZWmuccXRG_VBzBz_SUu-Nq16340Lgkyp
#json loads - used to valid output: https://docs.python.org/3/library/json.html#json.loads
#raw_decode - reads the first JSON object and ignores text around it: https://docs.python.org/3/library/json.html#json.JSONDecoder.raw_decode
#example domains for use: https://www.rfc-editor.org/info/rfc2606/
#25 second wait for OpenRouter - https://requests.readthedocs.io/en/latest/user/quickstart/#timeouts

import json, os, random, requests
from datetime import datetime

openRouterUrl = "https://openrouter.ai/api/v1/chat/completions"
timeoutSeconds = 90 #TEMPORARY FOR MODEL QUESTION GENERATION
questionCount = 5
scenarioTypes = ["email", "sms", "call", "social", "popup"]
promptFolder = os.path.join(os.path.dirname(__file__), "data", "prompts")

#Character lengths
scenarioMax = 800
questionMax = 300
optionMax = 200
explanationMax = 600

allowedDomains = ["example.com", "example.org", "example"]

#Used to avoid confusion with URLs and filenames
skippedWords = ["e.g", "i.e"]
fileEndings = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".exe", ".txt", ".jpg", ".png", ".html"]

#Used for every fail / error via OpenRouter. If this is called, the app uses stored questions instead
class ScenarioError(Exception):
    pass

#Creates a line to the log file, whether the model passes or fails any validation checks.
def writeLog(text):
    with open(os.path.join(os.path.dirname(__file__), "generation.log"), "a", encoding="utf-8") as logFile:
        logFile.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + text + "\n")



# - - - - - - - - - - 
# BUILDING PROMPTS
# - - - - - - - - - - 

def promptExists(slug):
    return os.path.isfile(os.path.join(promptFolder, os.path.basename(slug) + ".txt"))

#Module = row from modules table, references = row from module_references table, difficulty = "easy","medium" or "hard" (lowercase)
def buildPrompt(module, references, difficulty):
    fileName = os.path.basename(module["slug"]) + ".txt"

    try:
        with open(os.path.join(promptFolder, fileName), encoding="utf-8") as promptFile:
            prompt = promptFile.read()
    except OSError: #missing files
        raise ScenarioError("No prompt file for " + module["slug"])

    #Model chooses an id from this list to find a reference (format: id | source | title)
    referenceLines = ""
    for reference in references:
        referenceLines = referenceLines + str(reference["id"]) + " | " + reference["source"] + " | " + reference["title"] + "\n"

    moduleText = "WHAT IS IT:\n" + module["what_it_is"] + "\n\nHOW TO SPOT IT:\n" + module["how_to_spot"] + "\n\nHOW TO AVOID IT:\n" + module["how_to_avoid"]

    prompt = prompt.replace("<<DIFFICULTY>>", difficulty)
    prompt = prompt.replace("<<MODULE_TEXT>>", moduleText)
    prompt = prompt.replace("<<REFERENCES>>", referenceLines)
    return prompt



# - - - - - - - - - - 
# CALLING OPENROUTER API
# - - - - - - - - - - 

#Return text of OpenRouter's reply. If it is down or unresponsive, throw an error
def askOpenRouter(prompt):
    key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL")

    if not key or not model:
        raise ScenarioError("No API key or model available")

    try:
        response = requests.post(
            openRouterUrl,
            headers={"Authorization": "Bearer " + key},
            json = {"model": model, "messages": [{"role": "user", "content": prompt}]},
            timeout=timeoutSeconds #25 seconds before timing out
        )
    except requests.Timeout:
        raise ScenarioError("OpenRouter timed out")
    except requests.RequestException:
        raise ScenarioError("Network error")

    #429 = Limit exceeded (50 requests a day, 20 a minute).
    if response.status_code != 200:
        raise ScenarioError("http " + str(response.status_code))

    try:
        reply = response.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        raise ScenarioError("Unexpected reply format")

    if not isinstance(reply, str) or reply.strip() == "":
        raise ScenarioError("Empty reply")

    return reply




# - - - - - - - - - - 
# VALIDATING OPENROUTER RESPONSE
# - - - - - - - - - - 

#Validates URL address
def isAllowedAddress(address):
    address = address.lower()
    for domain in allowedDomains:
        if address == domain or address.endswith("." + domain):
            return True
    return False

#Returns the address part of the link (removes http and everything past the link (e.g. http://examplehack.example/important --> examplehack.example))
#Addresses typically  end with /, ? or #
def getLinkHost(link):
    host = link.split("://")[-1]
    for separator in ["/", "?", "#"]:
        host = host.split(separator)[0]
    return host.split(":")[0]

#Validates each piece of text against what was stated in the prompt (RULES / GUIDELINES)
#Field = output format field from prompt, value = content from the field
def checkText(value, field, maxLength):
    if type(value) != str or value.strip() == "":
        raise ScenarioError(field + " is empty or not a string")

    if len(value) > maxLength:
        raise ScenarioError(field + " is too long")

    #Cannot be 7 or more digits in a phone, account or card number
    digitsInARow = 0
    for character in value:
        if character.isdigit():
            digitsInARow = digitsInARow+1
            if digitsInARow >= 7:
                raise ScenarioError(field + " has too long of a number" + character)
        else:
            digitsInARow = 0 

    #No real URLs or email addresses (checks every word)
    for word in value.split():
        word = word.strip(".,;:!?()[]<>\"'").lower() 
        word = word.lstrip("$€£")

        #A link is allowed only if its an example address (not real)
        if word.startswith("http://") or word.startswith("https://") or word.startswith("www."):
            host = getLinkHost(word)
            if "@" in host or not isAllowedAddress(host):
                raise ScenarioError(field + " has a real link:" + host)
            continue

        if "@" in word:
            if not isAllowedAddress(getLinkHost(word.split("@")[-1])):
                raise ScenarioError(field + " has a real email address:" + word)
            
        elif "." in word and word not in skippedWords:
            #A word with a "/" in it is an address with a path
            isFile = False
            if "/" not in word:
                for ending in fileEndings:
                    if word.endswith(ending):
                        isFile = True

            isNumber = word.replace(".", "").isdigit() #e.g. 3.5
            if not isFile and not isNumber and not isAllowedAddress(getLinkHost(word)):
                raise ScenarioError(field + " has a real URL:" + word)

       


#Turns the  text from the model into a list of 5 checked questions
#allowedIds = reference ids sent into the prompt
def checkQuestions(reply, allowedIds):
    #Takes only the JSON structure and ignores the rest
    start = reply.find("{")
    if start == -1:
        raise ScenarioError("No JSON structure found")

    try:
        data, _ = json.JSONDecoder().raw_decode(reply[start:])
    except ValueError:
        raise ScenarioError("JSON could not be read")

    if type(data) != dict or type(data.get("questions")) != list:
        raise ScenarioError("Questions not in dictionary or list format")

    if len(data["questions"]) != questionCount:
        raise ScenarioError("Invalid number of questions")

    checked = [] #verified questions

    #Takes each column inside of questions and verifies each of them
    for item in data["questions"]:
        if type(item) != dict:
            raise ScenarioError("Question is not an object")

        if item.get("scenario_type") not in scenarioTypes:
            raise ScenarioError("Scenario type not allowed")

        checkText(item.get("scenario"), "scenario", scenarioMax)
        checkText(item.get("question"), "question", questionMax)
        checkText(item.get("explanation"), "explanation", explanationMax)

        options = item.get("options")
        if type(options) != list or len(options) != 4:
            raise ScenarioError("There must be 4 options")

        for option in options:
            checkText(option, "option", optionMax)

        if len(set(options)) != 4:
            raise ScenarioError("Options are not different")

        if type(item.get("correct_index")) != int or item["correct_index"] < 0 or item["correct_index"] > 3:
            raise ScenarioError("correct_index must be 0 to 3")

        if type(item.get("reference_id")) != int or item["reference_id"] not in allowedIds:
            raise ScenarioError("reference_id is not in the list sent")

        #The model tends to put the correct option first, so shuffle in code and find where it ended up
        correctText = options[item["correct_index"]]
        shuffledOptions = list(options)
        random.shuffle(shuffledOptions)

        #Once verified, create the structure manually and drop off everything else
        checked.append({
            "scenario_type": item["scenario_type"],
            "scenario": item["scenario"],
            "question": item["question"],
            "options": shuffledOptions,
            "correct_index": shuffledOptions.index(correctText),
            "explanation": item["explanation"],
            "reference_id": item["reference_id"]
        })
    return checked


# - - - - - - - - - - 
# CALLING ALL THREE SECTIONS (CREATE AND BUILD PROMPT, CALL OPENROUTER FOR RESPONSE, VERIFY THE RESPONSE AND RETURN THE QUESTIONS)
# - - - - - - - - - - 
def generateQuestions(module, references, difficulty):
    try:
        prompt = buildPrompt(module, references, difficulty)
        reply = askOpenRouter(prompt)
        questions = checkQuestions(reply, [reference["id"] for reference in references])
    except ScenarioError as error:
        writeLog("FAIL module=" + module["slug"] + " difficulty=" +difficulty + " reason=" +str(error) + " model=" + str(os.getenv("OPENROUTER_MODEL")))
        raise

    writeLog("PASS module=" + module["slug"] + " difficulty=" + difficulty + " model=" + str(os.getenv("OPENROUTER_MODEL")))
    return questions


