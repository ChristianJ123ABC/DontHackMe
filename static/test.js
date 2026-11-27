


//TEST PAGES SCRIPTS (module page "Take the test" button, test question page)

//Start test button (module page). Generating the questions can take up to 30 seconds, so the button is disabled after one click. This stops a second click from sending a second request to OpenRouter
const startTestForm = document.getElementById("startTestForm");
const startTestButton = document.getElementById("startTestButton");
const waitMessage = document.getElementById("waitMessage");

if (startTestForm) {
    startTestForm.addEventListener("submit", function () {
        startTestButton.disabled = true;
        waitMessage.hidden = false;
    });
}

//Answer button (question page). Stops the same answer being sent twice with a double click
const answerForm = document.getElementById("answerForm");
const answerButton = document.getElementById("answerButton");

if (answerForm) {
    answerForm.addEventListener("submit", function () {
        answerButton.disabled = true;
    });
}