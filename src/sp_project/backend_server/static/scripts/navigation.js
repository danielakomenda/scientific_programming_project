function generateNavbar() {
    setActiveNavbarItem()
    const nav = document.createElement('nav');
    nav.className = "navi navbar navbar-expand-sm";
    nav.style.backgroundColor ="";
    nav.innerHTML = `
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarTogglerDemo02" aria-controls="navbarTogglerDemo02" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>      
      <div class="collapse navbar-collapse" id="navbarTogglerDemo02">
        <ul class="navbar-nav mr-auto lg-2 mt-lg-0">
         <li class="nav-item">
            <a class="nav-link" href="main.html">Main</a>
         </li>
          <li class="nav-item">
            <a class="nav-link" href="weather_historic.html">Historic Weather</a>
          </li>
          <li class="nav-item">
          <a class="nav-link" href="weather_prediction.html">Weather Prediction</a>
        </li>
          <li class="nav-item">
            <a class="nav-link" href="energy_historic.html">Historic Energy-Generation</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="energy_model_prediction.html">Energy-Generation Prediction</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="extra.html">Extra</a>  
          </li>
        </ul>
      </div>
    `;
  
    // Create the Bootstrap CSS link element
    const cssLink = document.createElement('link');
    cssLink.rel = "stylesheet";
    cssLink.href = "https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css";
    nav.appendChild(cssLink);
  
    // Create the Bootstrap JS link element
    const jsLink = document.createElement('script');
    jsLink.src = "https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js";
    nav.appendChild(jsLink);
  
    document.body.appendChild(nav);
}

function setActiveNavbarItem() {
    const navbarItems = document.querySelectorAll('.navbar-nav a');
    const currentUrl = window.location.href;
    navbarItems.forEach(item => {
      if (item.href === currentUrl) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });
  }