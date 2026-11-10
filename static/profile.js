//PROFILE PAGE SCRIPTS (Delete, Regenerate codes, Re-activate 2FA, Edit Profile)
//Sources:
//Popup help (<dialog>)
//https://www.w3schools.com/jsref/met_dialog_showmodal.asp
//https://developer.mozilla.org/en-US/play?uuid=2d5ffb49648aeda7dcd8b20ae93ca41dbcc45e6e&state=pVVti%2BM2EP4rg7pQ50jtuw%2Bl4HUCt9srLbQc3B7tF0FXsSaJurLkynKyIeS%2Fl5Hki3eTywWaD7E97%2FM8o9GerX2jWckqqYS2K1Byxll852zODUC16L23JmpqbTvkDPyuxRlnUcXZ%2FJ7kVRG%2Fo9vSugYa9Gs7DhnDkC6FB6ja9AJQabFADUvryEhsfhBGNUJzNv9FbKxTHiFKyqoIpkfPDjXWPoUfeYIRDZW6FJv3g8jhv71yKL94A1S29cqaeVWkl1PVnVMGoVs71bQXzD6hhFYYKS7YPLRKooPGmifcndhVRWxmwKcYAKqk2hytxrx0%2FaJR%2FkjM8D2%2Ft2apXPOCGgo5RKoK4mLODYmIojk33LyIbVskij%2B2aCDajKJVrcNoFiemKlqHc27YlNVdx0r2HU3VnlKtUa3WvoR3P71tn29JYjfoltpuS%2BhqZ7UOwlZIqcyqhLf5jw6bIFtYJ9GV8K59hs5qJWGhRf10y80hpPqHMtXWdB60XX3Q2KDxMANp655e8xX6JL3b%2FSazVO3klptlb2pCnxwzj89%2BEqs9xsmVMeg%2B4zNFfLzZn9Mcbvbke%2BDcPIaKR0axt8%2B2hdmp%2BNcASmwkNpAO4qXih8NE9Ucn4ugucnbJMVJJbtwUBQRKE9Wk6kBAY6XQqQhujnFzIeWHDRr%2Fu%2Bo8GnQZbQNVP3E2hWwCs%2FkX3LLH6F5Ct7bbPyhgNnmkrJAC5yMF9U5%2FRQFhiwwFhVXTgV%2FjAMnCPg%2F9BuUVDad9FYA6ulzbSyrWoe%2Bd%2BVPoHmEGnHF2C0UBn7BDD1EJG9Ke9B9yvu49CYOoKOC99uiM8GqDejeFLUJtey2h74bGc9pX2PkAT0b5J7ewVX4NwgA2rd%2B9qCIfARpP%2FytIh1W%2FJHDp%2BBLvceUoa%2FIB47DAL4Ebt%2FhxCGOIa07feEGHQ2hdc46UYY2dThh5lBD1Cd6igAf0YWDGcIC3QRarQwlx2x4ZO8vyi17yYDsk%2BQtBWvO9B4MoKXqAdTyohGoyjhV6ZVbBIGAaqDu9GbdKa5BUrPAgem8b4VUttN7lKdjJAAWek%2FTsTIfpn0KGpHkFYdD%2BHTQlZKcolMDZzf5UfuAsTvS3sgtTo%2F56%2BqD%2BP%2FmvO6CJ528U6%2B1qpb%2BOVVRDKtbg9sELjyXc7IMoHySHa4BZ4NI6vJyRh3v6cWw6ZLdavso%2BSA7Ti6VNKWhc%2FmGc7oXWMWjeuvD8GZei1z6b0FgnGYhhrOkyUGYVvN%2FEAtUSsm5N%2B%2Bo%2B0JlN0vUZf%2BeDB%2BoADvR4UyS42JT5NTbISiaFe2KH%2FwA%3D&srcPrefix=%2Fen-US%2Fdocs%2FWeb%2FAPI%2FHTMLDialogElement%2F
//Close form: https://developer.mozilla.org/en-US/docs/Web/API/HTMLFormElement/reset
//Forcing uppercase for delete confirm text: https://stackoverflow.com/questions/11100041/why-isnt-text-transform-uppercase-working-to-set-my-input-text-to-uppercase

//Enabling the delete button only when the user types "DELETE" in the input field:
//https://flaviocopes.com/how-to-disable-button-javascript/
//Re-checks so the delete button reacts to the any changes: https://developer.mozilla.org/en-US/docs/Web/API/Element/input_event


//Custom data attributes (open/close-data-dialog)
//https://developer.mozilla.org/en-US/docs/Web/HTML/How_to/Use_data_attributes

///
// DELETE ACCOUNT POPUPS
///
const openDeleteForm = document.getElementById("openDeleteForm");
const closeDeleteForm = document.getElementById("closeDeleteForm");
const unsureDialog = document.getElementById("unsureDialog");

const deleteDialog = document.getElementById("deleteDialog");
const deleteForm = document.getElementById("deleteForm");

const confirmTextInput = document.getElementById("confirmText");
const confirmDelete = document.getElementById("confirmDelete");
const understand = document.getElementById("understand");


openDeleteForm.addEventListener("click", function () {
    unsureDialog.showModal();
});

unsureDialog.querySelector("#proceed").addEventListener("click", function () { //Query selector is used for the button only. addEventListener makes it so they can click the entire page and proceed
    unsureDialog.close();
    deleteDialog.showModal();
});

closeDeleteForm.addEventListener("click", () => {
    deleteDialog.close();
});

//Enable the delete button only when the user types "DELETE" in the input field and checks the checkbox
const updateDeleteButton = () => {
    if (confirmTextInput.value === "DELETE" && understand.checked) {
        confirmDelete.disabled = false;
    } else {
        confirmDelete.disabled = true;
    }
};

//Re-checks so the delete button reacts to the any changes
confirmTextInput.addEventListener("input", updateDeleteButton);
understand.addEventListener("change", updateDeleteButton);

//Wipes form data and disables the delete button when the dialog is closed
deleteDialog.addEventListener("close", function () {
    deleteForm.reset();
    confirmDelete.disabled = true;
});


///
// REGENERATE CODES AND RE-ACTIVATE 2FA POPUPS
///

//Makes any button with the data open dialog="id" open that dialog ID
document.querySelectorAll("[data-open-dialog]").forEach(function (button) {
    button.addEventListener("click", function () {
        document.getElementById(button.dataset.openDialog).showModal();
    });
});


//Makes any button with the data close dialog="id" close that dialog ID
document.querySelectorAll("[data-close-dialog]").forEach(function (button) {
    button.addEventListener("click", function () {
        document.getElementById(button.dataset.closeDialog).close();
    });
});


//Wipes form fields when dialog is closed
document.querySelectorAll("#regenDialog, #reactivateDialog").forEach(function (dialog) {
    dialog.addEventListener("close", function () {
        const form = dialog.querySelector("form");
        if (form){
            form.reset();
        }
    });
});