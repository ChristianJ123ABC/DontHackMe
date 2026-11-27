#Difficulty threshold:
#Easy = 0-39%
#Medium = 40-69%
#Hard = 70%+
#Averages not not rounded (69.9 != hard)

easy = 40
medium = 70


#Returns easy, medium or hard depending on the user's last 3 latest scores for the module
def getDifficulty(scores):
    #If user is brand new, make the starting difficulty easy
    if not scores:
        return "easy"

    average = sum(scores) / len(scores)

    if average < easy:
        return "easy"

    if average < medium:
        return "medium"

    return "hard"