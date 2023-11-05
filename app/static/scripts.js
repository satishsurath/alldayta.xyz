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