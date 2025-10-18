/* 
search for Fall/Spring [Year] schedule. Then open the console and run the code below. 
this code will print a json of all the classes being offered
*/



// Assuming jQuery and DataTables are loaded on the page
// Run this in the browser console on the page with the table

// Get the DataTable instance
const table = $('#classSchedule').DataTable();

// Get all row data (even across pages, since client-side)
const data = table.rows().data().toArray();

// Get headers
const headers = [];
$('#classSchedule thead th').each(function() {
  headers.push($(this).text().trim());
});

// Clean up function for cell content (remove HTML, get text, trim)
function cleanCell(cell) {
  if (typeof cell === 'string') {
    // Create a temp div to parse HTML and get text
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = cell;
    let text = tempDiv.textContent || tempDiv.innerText || '';
    // Special handling for multi-line like Days/Times if needed
    text = text.replace(/\n/g, ' ').trim();
    return text;
  }
  return cell;
}

// Map to array of objects
const courses = data.map(row => {
  const obj = {};
  headers.forEach((header, index) => {
    obj[header] = cleanCell(row[index]);
  });
  return obj;
});

// Output as JSON (you can copy this from console)
console.log(JSON.stringify(courses, null, 2));

// If you want to download as file (optional)
const blob = new Blob([JSON.stringify(courses, null, 2)], { type: 'application/json' });
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'all_courses.json';
a.click();
URL.revokeObjectURL(url);