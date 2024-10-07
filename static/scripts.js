function searchEvents(event) {
  event.preventDefault();
  const searchQuery = document.getElementById('search-events').value;
  alert('Searching for events related to: ' + searchQuery);
}

function searchCategory(categoryName) {
  alert('Searching for events in category: ' + categoryName);
}
