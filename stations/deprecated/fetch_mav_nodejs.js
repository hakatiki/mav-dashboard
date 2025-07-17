#!/usr/bin/env node

/**
 * MAV Stations Fetcher using the original mav-stations Node.js package
 * This script uses the martinlangbecker/mav-stations package
 */

const fs = require('fs').promises;
const path = require('path');

async function fetchMAVStations() {
    try {
        console.log('🚂 Fetching MAV stations using mav-stations package...');
        
        // Import the mav-stations package
        let mavStations;
        try {
            mavStations = require('mav-stations');
        } catch (error) {
            console.error('❌ mav-stations package not found!');
            console.log('📦 Please install it first with: npm install mav-stations');
            console.log('💡 Or use the Python version instead: python stations/mav_stations_fetcher.py');
            return false;
        }

        const stations = [];
        let count = 0;

        console.log('📡 Reading stations stream...');
        
        // Read stations from the stream
        for await (const station of mavStations.readStations()) {
            stations.push(station);
            count++;
            
            // Progress indicator
            if (count % 100 === 0) {
                console.log(`📍 Processed ${count} stations...`);
            }
        }

        console.log(`✅ Successfully fetched ${stations.length} MAV stations!`);

        // Save to JSON file
        const outputFile = path.join(__dirname, 'mav_stations_nodejs.json');
        await fs.writeFile(outputFile, JSON.stringify(stations, null, 2), 'utf8');
        
        // Create summary
        const summary = {
            total_stations: stations.length,
            countries: [...new Set(stations.map(s => s.country))],
            international_stations: stations.filter(s => s.isInternational).length,
            generated_at: new Date().toISOString(),
            sample_stations: stations.slice(0, 5),
            package_used: 'mav-stations (Node.js)',
            source: 'https://github.com/martinlangbecker/mav-stations'
        };

        const summaryFile = path.join(__dirname, 'mav_stations_nodejs_summary.json');
        await fs.writeFile(summaryFile, JSON.stringify(summary, null, 2), 'utf8');

        console.log(`📁 Data saved to: ${outputFile}`);
        console.log(`📊 Summary saved to: ${summaryFile}`);
        console.log(`🇭🇺 Found ${summary.international_stations} international stations`);
        
        return true;

    } catch (error) {
        console.error('❌ Error fetching MAV stations:', error.message);
        return false;
    }
}

// Package.json content for easy setup
const packageJsonContent = {
    "name": "mav-stations-fetcher",
    "version": "1.0.0",
    "description": "Fetch MAV stations data",
    "main": "fetch_mav_nodejs.js",
    "scripts": {
        "fetch": "node fetch_mav_nodejs.js",
        "install-deps": "npm install mav-stations"
    },
    "dependencies": {
        "mav-stations": "^0.3.4"
    },
    "keywords": ["mav", "stations", "hungary", "railway", "transport"],
    "author": "",
    "license": "ISC"
};

async function createPackageJson() {
    const packageJsonPath = path.join(__dirname, 'package.json');
    try {
        await fs.access(packageJsonPath);
        console.log('📦 package.json already exists');
    } catch {
        await fs.writeFile(packageJsonPath, JSON.stringify(packageJsonContent, null, 2));
        console.log('📦 Created package.json');
    }
}

async function main() {
    console.log('🚀 MAV Stations Fetcher (Node.js version)');
    console.log('Using martinlangbecker/mav-stations package\n');
    
    await createPackageJson();
    
    const success = await fetchMAVStations();
    
    if (!success) {
        console.log('\n💡 Setup instructions:');
        console.log('1. cd stations/');
        console.log('2. npm install mav-stations');
        console.log('3. node fetch_mav_nodejs.js');
        console.log('\nAlternatively, use the Python version:');
        console.log('python mav_stations_fetcher.py');
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = { fetchMAVStations }; 