function setUpMap() {
    var map = L.map('map').setView([47, 8], 8);

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);


    var marker = undefined; // L.marker().addTo(map);

    function onMapClick(e) {
        console.log("You clicked the map at " + e.latlng);
        if(marker === undefined){
          marker = L.marker(e.latlng).addTo(map);
        } else {
          marker.setLatLng(e.latlng);
        }
        $.get("/prediction-plot", {lat:e.latlng.lat, lon:e.latlng.lng}, function( data ) {
          console.log( "Load was performed." );
          const plots_div = $("#plots");
          plots_div.empty();
          if(data.plot !== undefined){
              Bokeh.embed.embed_item(data.plot, "plots");
          } else {
            plots_div.append("<h1>"+data.error+"</h1>");
            plots_div.append("<pre>"+data.traceback+"</pre>");
          }
        })
    }

    map.on('click', onMapClick);

}