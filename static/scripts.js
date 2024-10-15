function searchEvents() {
  event.preventDefault();

        // Get the value from the input field
        const searchInput = document.getElementById('search-events').value;

        window.location.href = `/browse.html?event=${encodeURIComponent(searchInput)}`;

        // Prevent form submission
        return false;
}

function searchCategory(categoryName) {
   window.location.href = `/browse.html?event=${encodeURIComponent(categoryName)}`;
}
