const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');
const container = document.getElementById('container');

signUpButton.addEventListener('click', () => {
    container.classList.add("right-panel-active");
});

signInButton.addEventListener('click', () => {
    container.classList.remove("right-panel-active");
});

function toggleFields() {
    const role = document.querySelector('input[name="role"]:checked').value;

    // Hide all dynamic fields first
    document.querySelectorAll('.dynamic-field').forEach(field => {
        field.style.display = 'none';
        field.querySelectorAll('input').forEach(input => input.required = false);
    });

    // Show relevant field
    if (role === 'student') {
        const field = document.getElementById('field-student');
        field.style.display = 'block';
        // field.querySelector('input').required = true; // Optional logic if strict
    } else if (role === 'alumni') {
        const field = document.getElementById('field-alumni');
        field.style.display = 'block';
    } else if (role === 'management') {
        const field = document.getElementById('field-management');
        field.style.display = 'block';
    }
}

// Initialize fields on load
document.addEventListener('DOMContentLoaded', () => {
    toggleFields();
});