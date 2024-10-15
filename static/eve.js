// eve.js


// Search events based on input
function searchEvents() {
  const query = document.getElementById('search-events').value;
  if (query) {
    window.location.href = `/browse.html?event=${query}`;
  }
}

function filterEvents() {
    const selectedCategories = Array.from(document.querySelectorAll('input[name="category"]:checked'))
        .map(checkbox => checkbox.value)
        .join('+');
    if (selectedCategories) {
        window.location.href = `/browse.html?event=${selectedCategories}`;
    }
}

// Add an event listener for each checkbox
document.querySelectorAll('input[name="category"]').forEach(checkbox => {
    checkbox.addEventListener('change', filterEvents);
});

function scheduleEvent(eventTitle, eventDate) {
            alert("Scheduling event: " + eventTitle + " on " + eventDate);
            // Implement logic to schedule the event on the calendar
}