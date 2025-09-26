/* 

run all_sjsu_courses_page_expander.js first.
running that code will expand all 54 pages of courses into one single page. 
then run this code to return the title and the course name in a json format.

*/

(function() {
    console.log("🚀 Starting course extraction script...");

    // 1. Select all the course links on the page.
    const courseLinks = document.querySelectorAll('a[href*="preview_course_nopop.php"]');
    
    if (courseLinks.length === 0) {
        console.error("❌ No course links found. Did you load the full list first?");
        alert("Error: No course links found. Make sure the full course list is visible before running this script.");
        return;
    }

    // 2. Create an array to hold the extracted course objects.
    const coursesData = [];
    
    // 3. Loop through each link found.
    courseLinks.forEach(link => {
        // Get the full text and clean up extra spaces
        const fullText = link.textContent.replace(/\s+/g, ' ').trim();
        
        // Split the text at the " - " separator
        const parts = fullText.split(' - ');
        
        // 4. Check if the split was successful
        if (parts.length === 2) {
            const courseCode = parts[0].trim();
            const courseName = parts[1].trim();
            
            // 5. Create a structured object with the requested keys and add it to the array.
            coursesData.push({
                title: courseCode,  // Changed from "courseCode"
                course: courseName  // Changed from "courseName"
            });
        } else {
            console.warn(`Could not parse the following course link text: "${fullText}"`);
        }
    });
    
    // 6. Convert the array of objects into a nicely formatted JSON string.
    const jsonOutput = JSON.stringify(coursesData, null, 2);
    
    // 7. Print the final JSON to the console.
    console.log(jsonOutput);
    
    // 8. (Bonus) Try to copy the JSON to the user's clipboard.
    try {
        navigator.clipboard.writeText(jsonOutput);
        console.log(`✅ Success! ${coursesData.length} courses extracted. The JSON output with 'title' and 'course' keys has been printed above and copied to your clipboard.`);
    } catch (err) {
        console.warn('Could not automatically copy to clipboard. You can select and copy the JSON output above manually.');
    }

})();