function setUpMap() {

    var map = L.map('map').setView([47, 8], 8);
    var marker = undefined;

    function onMapClick(e) {
        console.log("You clicked the map at " + e.latlng);
        if(marker === undefined){
          marker = L.marker(e.latlng).addTo(map);
        } else {
          marker.setLatLng(e.latlng);
        }

        $.get("/Energy-Prediction", {lat:e.latlng.lat, lon:e.latlng.lng}, function( data ) {
          console.log( "Load was performed." );
          const plots_div = $("#Energy-Prediction");
          plots_div.empty();
          if(data.energy_prediction_plot1 !== undefined){
              Bokeh.embed.embed_item(data.energy_prediction_plot1, "energy-prediction-plot");
              Bokeh.embed.embed_item(data.energy_prediction_plot2, "energy-prediction-plot");
          } else {
            plots_div.append("<h1>"+data.error+"</h1>");
            plots_div.append("<pre>"+data.traceback+"</pre>");
          }
        })

         $.get("/Weather-Prediction", {lat:e.latlng.lat, lon:e.latlng.lng}, function( data ) {
          console.log( "Load was performed." );
          const plots_div = $("#Weather-Prediction");
          plots_div.empty();
          if(data.weather_prediction_plot !== undefined){
              Bokeh.embed.embed_item(data.weather_prediction_plot, "weather-prediction-plot");
          } else {
            plots_div.append("<h1>"+data.error+"</h1>");
            plots_div.append("<pre>"+data.traceback+"</pre>");
          }
        })

    }


    $.getJSON('/static/scripts/switzerland-boundary.geo.json').then(function(swissBoundary) {
      var osm = L.TileLayer.boundaryCanvas("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        boundary: swissBoundary,
        attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors, CH shape <a href="https://github.com/johan/world.geo.json">johan/word.geo.json</a>'
      });
      map.addLayer(osm);
      var chLayer = L.geoJSON(swissBoundary);
      map.fitBounds(chLayer.getBounds());

      var clickableLayer = L.geoJson(swissBoundary, {
          onEachFeature: function(feature,layer){
            layer.on('click', function(evt) {
              onMapClick(evt);
            });
          },
          style: function (feature) {
            return {
              color: "#45E",
              fill: true,
              weight: 2,
              fillOpacity: 0
            };
          },
      }).addTo(map);
    });
}

