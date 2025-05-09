**Diary below**
# Blink 🚇⚡

Blink is a tap-to-pay transit app designed for Vietnam’s metro and VinBus network 🚍. Built from scratch during a 30-day coding bootcamp (on-my-own, self-taught), this app helps users plan routes, pay fares, and track rides in real-time. Powered by Python (FastAPI) for the backend, React Native (Expo) for the mobile frontend, PostgreSQL for data storage, Redis for caching, and Docker/Render for deployment—all using free tools! 💻 Features include route planning, fare management, real-time tracking, and future ML-powered arrival predictions. Let’s make transit smooth and smart! 🌍

## ✨ Features
- **Route Planning** 🗺️: Find the fastest path through Saigon’s metro using BFS-powered graph traversal—like going from Bến Thành to Suối Tiên in a snap!  
- **Tap-to-Pay** 💳: Pay your fares quickly with a single tap—works seamlessly with Vietnam’s metro and VinBus systems.  
- **Real-Time Tracking** 📍: Track your train with Redis-backed updates—never miss your ride again!  
- **Timetable Management** ⏰: Dynamic schedules with rush hour (5-min intervals) and late-night adjustments—Bến Thành stays open until midnight for those late-night vibes.  
- **ML Arrival Predictions** 🤖: Machine learning to predict train arrivals—coming soon to make your rides even smarter!  

## 🛠️ Tech Stack
- **Backend**: Python (FastAPI) for fast and scalable APIs 🐍  
- **Frontend**: React Native (Expo) for a smooth cross-platform mobile experience 📱  
- **Database**: PostgreSQL to store trip data securely 🗃️  
- **Cache**: Redis for real-time tracking with low latency ⚡  
- **Deployment**: Docker & Render for free cloud hosting ☁️  
- **Data Structures**: Arrays, hash tables, trees, and graphs to power route planning and more 📊  

## 🎨 Design/Sketch
Check out the design I created for Blink in Figma—it’s got all the vibes!
- **Banner**
![Blink App Banner](/readme/BlinkBanner.png)
- **NFC Home Screen**
![Blink App 1](/readme/BlinkNFCLight.png)
![Blink App 2](/readme/BlinkNFCDark.png)
- **QR Home Screen**
![Blink App 3](/readme/BlinkQRLight.png)
![Blink App 4](/readme/BlinkQRDark.png)

*Caption*: A mockup of the Blink app UI, featuring the route planner, timetable, and tap-to-pay screens. 🚉

## Diary
- **Day 1**
- Established/Created the project with all the tools needed: FastAPI, Redis (Python), React Native, Connection to Postgre server.
- Did research how to work with this techstack, what's to look out for and what are the better alternatives
- Created a station map and graph according to this image, also a timetable generated by AI that take accounts of rush hour depending on the area of the station and the route, some some like that I don't know how to explain but it takes account of other factors as well to generate a good timetable, I hope lol. 
![Metro Map](/readme/MetroMap.png)
- **Day 2**
- **Added backend functions:**
- add_trips (add an trip object contains start station and end station, pretty simple)
- find_path (use BFS algorithm to look for path from start to end, BFS doesn't take account of other variables such as time to wait for next train, or time to travel. Instead BFS just you know look for least amount of step to get to the end station as all step took the same amount of time.)
- get_station_id (enter the station name and retrieve the station's ID in the hash table. pretty simple)
- get_timetable
- **Run a good set of unit test on all these functions, had some problem with the station_map and station_graph working with the algorithms but eventually managed to be successful on all tests**
- **Day 3**
- Doing research with AI, exploring which algorithm will be used to be used as find_path that take accounts of travel time and waiting time at the station too (A* or Dijkstra).
- **Day 4**
- Been planning to migrate station_graph and station_map and schedules to PostgreSQL, doing research on building the database structure that contains all the fields needed while optimal at the same time. Also looking up Redis to implement live fetching for real-time features (eg. looking up trains that will be leaving soon, ...).
- Going back to the Figma design, prolly need some redo here and there, will most likely working on the color palette and some other shit as well.
