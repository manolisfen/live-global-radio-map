import React, { useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import axios from "axios";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});

function App() {
  const [stations, setStations] = useState([]);

  useEffect(() => {
    axios.get("/api/stations/Greece")
      .then(res => {
        const stationsWithLocation = res.data.filter(
          station => station.geo_lat && station.geo_long
        );
        setStations(stationsWithLocation);
      })
      .catch(err => console.error(err));
  }, []);

  return (
    <MapContainer center={[39.0742, 21.8243]} zoom={6} style={{ height: "100vh", width: "100%" }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {stations.map((station) => (
        <Marker key={station.stationuuid} position={[station.geo_lat, station.geo_long]}>
          <Popup>
            <strong>{station.name}</strong><br />
            {station.state && `(${station.state})`}<br />
            <audio controls src={station.url_resolved} style={{ width: "250px", marginTop: "10px" }} />
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}

export default App;