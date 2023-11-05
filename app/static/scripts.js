function setTheme(theme) {
    const root = document.documentElement;
    const body = document.body;
    if (theme === 'dark') {
        body.classList.add('dark-mode');
        root.style.setProperty('--bg-color', '#10141d');
        root.style.setProperty('--text-color', '#edf1fb');
        root.style.setProperty('--input-bg-color', '#444');
        root.style.setProperty('--input-text-color', '#edf1fb');
        root.style.setProperty('--button-bg-color', '#444');
        root.style.setProperty('--button-text-color', '#edf1fb');
    } else {
        body.classList.remove('dark-mode');
        root.style.setProperty('--bg-color', '#f2f3f7');
        root.style.setProperty('--text-color', '#10141d');
        root.style.setProperty('--input-bg-color', '#f2f3f7');
        root.style.setProperty('--input-text-color', '#10141d');
        root.style.setProperty('--button-bg-color', '#f2f3f7');
        root.style.setProperty('--button-text-color', '#10141d');
    }
    localStorage.setItem('theme', theme);
}

document.addEventListener('DOMContentLoaded', () => {
    applyTheme();

    const toggleSwitch = document.getElementById('toggle-theme');
    const savedTheme = localStorage.getItem('theme') || 'light';
    // toggleSwitch.checked = savedTheme === 'dark';

   // toggleSwitch.addEventListener('change', () => {
   //     const newTheme = toggleSwitch.checked ? 'dark' : 'light';
   //     setTheme(newTheme);
   // });

  // Get all details elements
  const detailsElements = document.querySelectorAll('details');

  // On page load, set the state from localStorage
  detailsElements.forEach((details) => {
      const isOpen = localStorage.getItem(details.id);
      if (isOpen !== null) {
          details.open = isOpen === "true"; // Convert the string to a boolean and set it
      }
  });

  // Listen for the toggle event and save the state to localStorage
  detailsElements.forEach((details) => {
      details.addEventListener('toggle', function() {
          localStorage.setItem(details.id, details.open);
      });
  });



});

function applyTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
}



function escapeSelector(s) {
    return s.replace(/(:|\.|\[|\]|,)/g, "\\$1");
}

function toggleActivation(fileName, courseName) {
    let csrfToken = $('meta[name="csrf-token"]').attr('content');
    
    console.log(`Attempting to toggle activation for course: ${courseName}, file: ${fileName}`);
    
    let encodedCourseName = encodeURIComponent(courseName);
    let encodedFileName = encodeURIComponent(fileName);
    //let link = $("#activation-" + fileName);
    let escapeFileName = escapeSelector(fileName)
    //let link = $("#activation-" + escapeFileName);
    let link = document.getElementById("activation-" + escapeFileName);
  
    //let elem = document.getElementById("activation-" + escapeFileName);
        if (link) {
            console.log("Element is in the DOM");
        } else {
            console.log("Element is NOT in the DOM");
        }



    console.log(`Encoding completed ${encodedCourseName}, file: ${encodedFileName}`);

    if(link) {
        console.log(`Found the link element for file: ${escapeFileName}`);
    } else {
        console.error(`Did not find any link element for file: ${escapeFileName}`);
    }

    $.ajax({
        url: "/toggle_activation/" + encodedCourseName + "/" + encodedFileName,
        type: 'POST',
        headers: {
            "X-CSRFToken": csrfToken
        },
        success: function(data) {
            if (data.success) {

                  console.log(`Received data.status: ${data.status}`);  
                    console.log(`Successfully toggled activation for file: ${fileName}. New status: ${data.status}`);
                if (data.status) {

                        console.log(`Attempting to change the SVG - for True ${link.innerHTML}`);
                        link.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" x="0px" y="0px" width="18px" height="18px" viewBox="0 0 20 25" style="enable-background:new 0 0 20 20;" xml:space="preserve"><style type="text/css">.st0{fill:none;stroke:#231F20;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;stroke-miterlimit:10;}</style><g><g><path d="M17,20H3c-1.7,0-3-1.3-3-3V3c0-1.7,1.3-3,3-3h14c1.7,0,3,1.3,3,3v14C20,18.7,18.7,20,17,20z M3,2C2.4,2,2,2.4,2,3v14    c0,0.6,0.4,1,1,1h14c0.6,0,1-0.4,1-1V3c0-0.6-0.4-1-1-1H3z"/></g><g><path d="M7.9,13.7l-3.1-3c-0.4-0.4-0.4-1,0-1.4c0.4-0.4,1-0.4,1.4,0l2.4,2.3l5.2-5.2c0.4-0.4,1-0.4,1.4,0s0.4,1,0,1.4l-5.9,5.9    C8.9,14.1,8.3,14.1,7.9,13.7z"/></g></g></svg>';  // SVG for Deactivate
                        console.log(`Successfully changed the SVG ${link.innerHTML}`);
                    } else {
                      console.log(`Attempting to change the SVG - for False: ${link.innerHTML}`);
                         link.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="18px" height="18px" viewBox="0 0 25 25" version="1.1" x="0px" y="0px"><title>2/icons/checkbox-off-24-black</title><desc>Created with Sketch.</desc><g stroke="none" stroke-width="1" fill="none" fill-rule="evenodd"><g fill-rule="nonzero" fill="#000000"><path d="M6,5 C5.44771525,5 5,5.44771525 5,6 L5,18 C5,18.5522847 5.44771525,19 6,19 L18,19 C18.5522847,19 19,18.5522847 19,18 L19,6 C19,5.44771525 18.5522847,5 18,5 L6,5 Z M6,3 L18,3 C19.6568542,3 21,4.34314575 21,6 L21,18 C21,19.6568542 19.6568542,21 18,21 L6,21 C4.34314575,21 3,19.6568542 3,18 L3,6 C3,4.34314575 4.34314575,3 6,3 Z"/></g></g></svg>  '; // SVG for Activate
                        // link.html('Test');  // SVG for Activate
                        console.log(`Successfully changed the SVG ${link.innerHTML}`);
                    }  

            } else {
                console.error("Error while toggling activation: " + data.error);
                console.error(`Failed to toggle activation for file: ${fileName}. Data success: ${data.success} Data Status: ${data.status} Error:  ${data.error}`);
            }
        },
        error: function(xhr, status, error) {
            console.error(`AJAX request failed with status: ${status}, error: ${error}`);
        }
    });
}

function showPreview(courseName, contentName, event) {
    // Get the CSRF token from the meta tag
    let csrfToken = $('meta[name="csrf-token"]').attr('content');
    
    // Encode the courseName
    let encodedCourseName = encodeURIComponent(courseName);
    
    // Remove the current file extension from contentName and append .csv
    let fileNameWithoutExtension = contentName.replace(/\.[^/.]+$/, "");
    let newContentName = fileNameWithoutExtension + "-originaltext.csv";
    
    // Encode the new contentName with .csv extension
    let encodedContentName = encodeURIComponent(newContentName);
    
    console.log(`Requesting preview for course: ${courseName}, content: ${newContentName}`);
    
    // AJAX Request to get the course preview
    $.ajax({
        url: `/preview-chunks-js/${encodedCourseName}/${encodedContentName}`,
        type: 'GET',
        headers: {
            "X-CSRFToken": csrfToken
        },
        success: function(data) {
            // Create tooltip HTML
            let tooltipHtml = `<div class="tooltip">${data.preview_content}</div>`;
            // Append tooltip HTML to the body
            $('body').append(tooltipHtml);
            
            // Calculate the left position based on the mouse event
            let leftPosition = event.pageX - $('.tooltip').width() - 10; // Adjust -10 for spacing
            
            // Set tooltip position to the bottom left corner
            $('.tooltip').css({
                top: event.pageY + 10 + 'px',
                left: leftPosition + 'px'
            });


    // Add mouseleave event to hide the tooltip when the mouse leaves it
    $('.tooltip').on('mouseleave', function() {
        hidePreview();
    });

    // Add an event listener to the document to hide the tooltip on any click
    $(document).on("click", function(e) {
            hidePreview(); // Hide the tooltip
        
    });

        },
        error: function(xhr, status, error) {
            console.error(`AJAX request failed with status: ${status}, error: ${error}`);
        }
    });
}


function hidePreview() {
    // Remove tooltip HTML from the body
    $('.tooltip').remove();
}

