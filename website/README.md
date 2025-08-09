# 🚆 MÁV Monitor

Modern, responsive dashboard for monitoring Hungarian railway traffic and delays.

## 🚀 Quick Start

### Live Demo
Visit the live website: **[https://mav-monitor.web.app](https://mav-monitor.web.app)**

## 📋 Table of Contents
- [Features](#features)
- [Local Development](#local-development)
- [Deployment](#deployment)
- [Usage](#usage)
- [Technical Details](#technical-details)
- [Future Enhancements](#future-enhancements)
- [Customization](#customization)

## Features

### 📊 **Dashboard Overview**
- **Summary Cards**: Quick overview of key metrics (total routes, average delay, on-time percentage, average price)
- **Interactive Histograms**: Delay distribution and ticket price analysis using Chart.js
- **Detailed Analysis**: Most problematic routes, performance metrics, and recommendations
- **Date Selection**: Choose any date (defaults to yesterday's data)

### 🎨 **Design**
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices
- **Modern UI**: Clean, professional interface with beautiful gradients and animations
- **Hungarian Language**: All interface elements and labels in Hungarian
- **MÁV Theme**: Color scheme inspired by Hungarian State Railways

### 📱 **Mobile Optimized**
- Touch-friendly controls
- Responsive charts that adapt to screen size
- Optimized layout for mobile viewing
- Fast loading and smooth interactions

## 🏃‍♂️ Local Development

### Prerequisites
- **Node.js** (v14 or higher) - [Download here](https://nodejs.org/)
- **Git** - [Download here](https://git-scm.com/)
- **Modern web browser** (Chrome, Firefox, Safari, Edge)

### Option 1: Simple Local Server (Recommended)

1. **Clone or download the project**
   ```bash
   # If using Git
   git clone <your-repo-url>
   cd website
   
   # Or simply navigate to the website folder
   cd website
   ```

2. **Start a local server**
   
   **Using Python (if installed):**
   ```bash
   # Python 3
   python -m http.server 8000
   
   # Python 2
   python -m SimpleHTTPServer 8000
   ```
   
   **Using Node.js:**
   ```bash
   # Install a simple HTTP server globally
   npm install -g http-server
   
   # Start the server
   http-server -p 8000
   ```
   
   **Using PHP (if installed):**
   ```bash
   php -S localhost:8000
   ```

3. **Open in browser**
   - Navigate to `http://localhost:8000`
   - The dashboard should load automatically

### Option 2: Using the Proxy Server (For CORS Testing)

If you need to test CORS functionality or API calls:

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Start the proxy server**
   ```bash
   npm start
   # or
   node proxy_server.js
   ```

3. **Access the website**
   - Main dashboard: `http://localhost:3000`
   - CORS proxy: `http://localhost:3000/cors_proxy.html`

### Option 3: Direct File Opening (Basic)

1. **Open directly in browser**
   - Double-click `index.html` or drag it into your browser
   - **Note**: Some features may not work due to CORS restrictions

## 🚀 Deployment

### Deploy to Firebase Hosting

#### Prerequisites
- **Firebase CLI** - Install globally:
  ```bash
  npm install -g firebase-tools
  ```

#### Step-by-Step Deployment

1. **Login to Firebase**
   ```bash
   firebase login
   ```

2. **Initialize Firebase (if not already done)**
   ```bash
   cd website
   firebase init hosting
   ```
   
   **Configuration options:**
   - Select "Use an existing project" → Choose `mav-monitor`
   - Public directory: `.` (current directory)
   - Single-page app: `No`
   - GitHub integration: `No`

3. **Deploy to Firebase**
   ```bash
   firebase deploy --only hosting
   ```

4. **Access your deployed site**
   - **Live URL**: https://mav-monitor.web.app
   - **Project Console**: https://console.firebase.google.com/project/mav-monitor/overview

#### Firebase Configuration Files

The project includes these Firebase configuration files:

- `firebase.json` - Hosting configuration
- `.firebaserc` - Project association
- `.gitignore` - Git ignore rules

#### Updating the Deployment

To update your deployed website after making changes:

```bash
# Make your changes to the files
# Then deploy again
firebase deploy --only hosting
```

### Alternative Deployment Options

#### Deploy to GitHub Pages

1. **Create a GitHub repository**
2. **Push your code**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

3. **Enable GitHub Pages**
   - Go to repository Settings → Pages
   - Select source branch (usually `main`)
   - Your site will be available at `https://<username>.github.io/<repo-name>`

#### Deploy to Netlify

1. **Drag and drop** the `website` folder to [Netlify](https://netlify.com)
2. **Or connect your GitHub repository** for automatic deployments

## Usage

### Getting Started
1. Open `index.html` in your web browser (or visit the deployed URL)
2. The dashboard will load with yesterday's data by default
3. Use the date picker to select a different date
4. Click "Adatok betöltése" to refresh the data

### Data Visualization
- **Delay Histogram**: Shows distribution of train delays in minutes
- **Price Histogram**: Shows distribution of ticket prices for paid routes
- **Analysis Section**: Displays most delayed routes, expensive routes, and performance metrics

### Current Implementation
- Uses **fake data** generated based on real MÁV patterns from your analysis notebook
- Data patterns match real statistics (47.8% on-time, average delays, price distributions)
- Ready to integrate with Google Cloud Storage data when available

## Technical Details

### Technologies Used
- **HTML5**: Semantic structure with Hungarian content
- **CSS3**: Modern styling with CSS Grid, Flexbox, and animations
- **JavaScript ES6+**: Object-oriented design with Chart.js integration
- **Chart.js**: Interactive, responsive charts
- **Google Fonts**: Inter font family for modern typography
- **Firebase**: Hosting and analytics
- **Tailwind CSS**: Utility-first CSS framework

### Browser Support
- Chrome/Edge 80+
- Firefox 75+
- Safari 13+
- Mobile browsers (iOS Safari, Chrome Mobile)

### File Structure
```
website/
├── index.html                    # Main dashboard page
├── script.js                     # Interactive functionality
├── map.html                      # Interactive map visualization
├── delay_aware_train_map.html    # Delay-aware map
├── max_delay_train_map.html      # Maximum delay map
├── cors_proxy.html               # CORS proxy page
├── proxy_server.js               # CORS proxy server
├── package.json                  # Node.js dependencies
├── firebase.json                 # Firebase hosting config
├── .firebaserc                   # Firebase project config
├── .gitignore                    # Git ignore rules
├── images/                       # Images and assets
├── node_modules/                 # Node.js dependencies
└── README.md                     # This file
```

## Future Enhancements

### Planned Features
- **Google Cloud Integration**: Connect to real MÁV data from your bucket
- **Map Integration**: Embed the `hungary_train_delays.html` map
- **Real-time Updates**: Auto-refresh data for current day monitoring
- **Export Features**: Download charts and reports as PDF/images
- **Advanced Filtering**: Filter by route, station, or delay severity

### Data Integration
The dashboard is designed to easily integrate with your existing data pipeline:

```javascript
// Replace fake data generation with real GCS data loading
async loadDataFromGCS(date) {
    const response = await fetch(`/api/mav-data/${date}`);
    return await response.json();
}
```

## Customization

### Colors
Modify the Tailwind config in `index.html` to change the color scheme:

```javascript
tailwind.config = {
    theme: {
        extend: {
            colors: {
                'mav-navy': '#002B51',
                'mav-blue': '#0057BE',
                'mav-light-blue': '#187ABA',
                'mav-lighter-blue': '#4695C8',
                'mav-success': '#059669',
            }
        }
    }
}
```

### Chart Configuration
Charts can be customized in `script.js` by modifying the Chart.js options.

## Troubleshooting

### Common Issues

**CORS Errors:**
- Use the proxy server: `npm start`
- Or deploy to Firebase for production

**Firebase Deploy Issues:**
- Ensure you're logged in: `firebase login`
- Check project association: `firebase projects:list`
- Verify configuration: `firebase use --add`

**Local Server Issues:**
- Try a different port if 8000 is busy
- Use `http-server -p 8080` for port 8080
- Check if Node.js is installed: `node --version`

**Proxy Server Port Conflicts:**
- If you get `EADDRINUSE: address already in use :::3000`:
  ```bash
  # Find the process using port 3000
  netstat -ano | findstr :3000
  
  # Kill the process (replace PID with the actual process ID)
  taskkill /PID <PID> /F
  
  # Or use a different port
  $env:PORT=3001; node proxy_server.js
  ```

## License

This project is created for MÁV (Magyar Államvasutak) traffic monitoring and analysis.

---

**Note**: This is a demonstration dashboard with simulated data. For production use, integrate with your Google Cloud Storage bucket containing real MÁV data. 