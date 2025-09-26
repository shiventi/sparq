/* 

run this on https://catalog.sjsu.edu/content.php?catoid=17&navoid=7688 to open all the 54 pages. 
then run all_sjsu_courses_title_course_json.js to extract the courses in json format.

*/

(async function() {
    console.log("🚀 Starting course aggregation script...");

    // --- 1. Find the main container for the course list ---
    const targetContainer = document.querySelector("#advanced_filter_section + table.table_default > tbody");
    if (!targetContainer) {
        console.error("❌ Could not find the course list container. The page structure may have changed.");
        alert("Script failed: Could not find the course list container.");
        return;
    }

    // --- 2. Determine the total number of pages ---
    let totalPages = 54; // Default fallback
    try {
        const lastPageLink = document.querySelector('a[aria-label^="Page "][href*="cpage="]:last-of-type');
        const pageNum = parseInt(lastPageLink.textContent.trim(), 10);
        if (!isNaN(pageNum)) {
            totalPages = pageNum;
        }
    } catch (e) {
        console.warn("Could not dynamically determine total pages. Falling back to 54.");
    }
    console.log(`- Found ${totalPages} pages to fetch.`);

    // --- 3. Display a loading message ---
    const originalFirstPageRows = [...targetContainer.querySelectorAll('tr')]; // Save page 1 content
    targetContainer.innerHTML = `
        <tr>
            <td colspan="2" style="text-align:center; padding: 40px; font-size: 1.5em;">
                <p><strong>⏳ Loading all ${totalPages} pages...</strong></p>
                <p id="progress-indicator" style="font-size: 0.8em; color: #555;">Fetching page 1 of ${totalPages}</p>
            </td>
        </tr>`;
    const progressIndicator = document.getElementById('progress-indicator');

    // --- 4. Function to fetch and parse a single page ---
    async function fetchPageContent(pageNumber) {
        // Build the URL for the next page
        const url = new URL(window.location.href);
        url.searchParams.set('filter[cpage]', pageNumber);
        
        try {
            const response = await fetch(url.toString());
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const htmlText = await response.text();
            
            // Use DOMParser to turn the HTML string into a document
            const parser = new DOMParser();
            const doc = parser.parseFromString(htmlText, 'text/html');
            
            // Extract only the course rows (<tr> elements) from the new document
            const pageContainer = doc.querySelector("#advanced_filter_section + table.table_default > tbody");
            return pageContainer ? [...pageContainer.querySelectorAll('tr')] : [];
        } catch (error) {
            console.error(`❌ Failed to fetch page ${pageNumber}:`, error);
            return []; // Return empty array on failure
        }
    }

    // --- 5. Fetch all pages concurrently ---
    const allCourseRows = [...originalFirstPageRows]; // Start with the content of the current page
    
    for (let i = 2; i <= totalPages; i++) {
        progressIndicator.textContent = `Fetching page ${i} of ${totalPages}...`;
        console.log(`- Fetching page ${i}...`);
        const rows = await fetchPageContent(i);
        allCourseRows.push(...rows);
    }

    console.log(`- Fetched a total of ${allCourseRows.length} rows.`);

    // --- 6. Replace the content with the full list ---
    console.log("✅ All pages fetched. Rendering the complete list...");
    targetContainer.innerHTML = ''; // Clear the "Loading..." message

    // Use a DocumentFragment for performance
    const fragment = document.createDocumentFragment();
    allCourseRows.forEach(row => {
        fragment.appendChild(row);
    });
    targetContainer.appendChild(fragment);
    
    // Remove the old pagination links as they are now irrelevant
    const pagination = targetContainer.nextElementSibling;
    if (pagination) {
        pagination.remove();
    }
    
    console.log("🎉 Done! The full course list is now displayed.");
    alert(`Success! All ${totalPages} pages have been loaded onto this single page. You can now use Ctrl+F to search or Ctrl+P to print.`);

})();