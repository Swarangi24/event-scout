function validation(){
    var x=document.eventForm.email.value;
    var atpos=x.indexOf("@");
    var dotpos=x.lastIndexOf(".");
    if(atpos<1 || dotpos<atpos+2 || dotpos+2 >= x.length){
        alert('Please enter valid email address');
        return false;
    }

}

function nextStep(step) {
    const currentStep = document.querySelector('.form-section.active');
    const inputs = currentStep.querySelectorAll('input, select, textarea');
    let allValid = true;

    // Validate current step fields
    inputs.forEach(input => {
        if (!input.checkValidity()) {
            allValid = false;
            input.reportValidity();
        }
    });

    if (!allValid) return;

    // Hide all form sections
    document.querySelectorAll('.form-section').forEach(section => {
        section.classList.remove('active');
    });

    // Show the current form section
    document.getElementById('step' + step).classList.add('active');

    // Update progress bar
    document.querySelectorAll('.progress-bar .circle').forEach((circle, index) => {
        if (index < step) {
            circle.classList.add('active');
        } else {
            circle.classList.remove('active');
        }
    });
}

function prevStep(step) {
    // Hide all form sections
    document.querySelectorAll('.form-section').forEach(section => {
        section.classList.remove('active');
    });

    // Show the previous form section
    document.getElementById('step' + step).classList.add('active');

    // Update progress bar
    document.querySelectorAll('.progress-bar .circle').forEach((circle, index) => {
        if (index < step) {
            circle.classList.add('active');
        } else {
            circle.classList.remove('active');
        }
    });
}

document.getElementById('eventForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const phone = document.getElementById('phone').value;
    const pincode = document.getElementById('pincode').value;

    if (!/^\d{10}$/.test(phone)) {
        alert('Please enter a valid 10-digit phone number.');
        return;
    }

    if (!/^\d{6}$/.test(pincode)) {
        alert('Please enter a valid 6-digit pin code.');
        return;
    }

    // Collect form data
    const formData = new FormData(document.getElementById('eventForm'));
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });

    // Send data to Flask API
            fetch('/event', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            })
            .then(response => response.json())
            .then(result => {
                if (result.message) {
                    alert(result.message);
                    // Redirect to the event details page
                    window.location.href = 'eventDetails.html';
                } else {
                    alert('An error occurred. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');

        });
});
