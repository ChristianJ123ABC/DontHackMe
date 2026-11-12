//Sources:
//Re-checks so every change reacts to typing: https://developer.mozilla.org/en-US/docs/Web/API/Element/input_event
//zxcvbn usage: https://github.com/dropbox/zxcvbn + https://www.jsdelivr.com/package/npm/zxcvbn + https://blogs.sagarsangwan.dev/blog/how-to-build-a-live-password-strength-meter-in-next-js-with-zxcvbn-js-1738166975873 + https://www.npmjs.com/package/zxcvbn-typescript
//Layout idea: https://bitwarden.com/password-strength/ + https://lowe.github.io/tryzxcvbn/
//Meter from Weak to Strong coloured: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/meter

const checkInput = document.getElementById("checkInput");
const strengthResult = document.getElementById("strengthResult");
const strengthMeter = document.getElementById("strengthMeter")
const strengthLabel = document.getElementById("strengthLabel");
const crackTime = document.getElementById("crackTime");
const lengthNotice = document.getElementById("lengthNotice");
const strengthError = document.getElementById("strengthError");

//Levels are the time to crack the password
const levels = ["Very Weak", "Weak", "Fair", "Good", "Strong"]

//Time to crack is compared in seconds
const day = 86400;
const month = day*31;
const year =  day * 31 * 12;
const century = year * 100;
const labels = [day, month, year, century];

//Only show strength check if password is inputted
checkInput.addEventListener("input", function() {
    if (checkInput.value === ""){
        strengthResult.hidden = true;
        return;
    }

    //If  CDN is blocked, display error message
    if (typeof zxcvbn === "undefined"){
        strengthResult.hidden = true;
        strengthError.hidden = false;
        return;
    }
    
    //Only scores the first 100 characters towards the strength
    const result = zxcvbn(checkInput.value.slice(0,100))

    //Compares the crack time against scrypt, the hash DontHackMe uses
    const seconds = result.crack_times_seconds.offline_slow_hashing_1e4_per_second;


    //For loop to see how many seconds it takes to crack, and applys a label to it
    let level = 0;
    for (let i = 0; i<labels.length; i++){
        if (seconds >= labels[i]){
            level = i + 1;
        }
    }

    //Meter goes from 0 - 4, ranging in colours on the meter
    strengthMeter.value = level;
    strengthLabel.textContent = levels[level];
    crackTime.textContent = result.crack_times_display.offline_slow_hashing_1e4_per_second;
    
    lengthNotice.hidden = checkInput.value.length >= 15;
    strengthResult.hidden = false;
});