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
                        link.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24"><path d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q8 0 15 1.5t14 4.5l-74 74H200v560h560v-266l80-80v346q0 33-23.5 56.5T760-120H200Zm261-160L235-506l56-56 170 170 367-367 57 55-424 424Z"/></svg>';  // SVG for Deactivate
                        loadFileInfo(courseName);
                        console.log(`Successfully changed the SVG ${link.innerHTML}`);
                    } else {
                      console.log(`Attempting to change the SVG - for False: ${link.innerHTML}`);
                         link.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24"><path d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm0-80h560v-560H200v560Z"/></svg>'; // SVG for Activate
                         loadFileInfo(courseName);
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
            let tooltipHtml = `<div class="tooltip">${data.preview_content}<br><br><span style="color:red;"><b>Click anywhere to hide this Preview<b></span></div>`;
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

function loadFileInfo(courseName) {
    $.ajax({
        url: `/course-file-info/${courseName}`,
        type: 'GET',
        success: function(response) {
            var file_info = response;
            var container = $('#file-info-container');
            container.empty(); // Clear existing contents

            $.each(file_info, function(file_name, file_details) {
                var fileHTML = '';

                if (file_details.present) {
                    fileHTML += '';
                } else {
                    fileHTML += '';
                }
                
                fileHTML += file_details.name + ' [Size: ';

                if (file_details.size) {
                    var sizeMB = (file_details.size / 1024 / 1024).toFixed(2);
                    fileHTML += sizeMB + ' MB';
                } else {
                    fileHTML += 'File not present';
                }

                fileHTML += ']';
                
                // Append each file info to the container
                container.append('<p>' + fileHTML + '</p>');
            });
        },
        error: function(xhr, status, error) {
            // Handle errors here
            console.log("An error occurred while retrieving file info:", error);
        }
    });
}




