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
- ![Blink App Banner](/readme/BlinkBanner.png)
- **NFC Home Screen**
- ![Blink App 1](/readme/BlinkNFCLight.png)
- ![Blink App 2](/readme/BlinkNFCDark.png)
- **QR Home Screen**
- ![Blink App 3](/readme/BlinkQRLight.png)
- ![Blink App 4](/readme/BlinkQRDark.png)

*Caption*: A mockup of the Blink app UI, featuring the route planner, timetable, and tap-to-pay screens. 🚉