/*

Use this to expand all GE courses on https://catalog.sjsu.edu/preview_program.php?catoid=17&poid=13657 

*/


// Select all the course links that are in a "collapsed" state.
// We can identify them because their onclick attribute contains the 'showCourse' function.
const allCourseLinks = document.querySelectorAll('a[onclick*="showCourse"]');

// Loop through each link found.
allCourseLinks.forEach(link => {
  // Simulate a click on each link to trigger the expansion.
  link.click();
});