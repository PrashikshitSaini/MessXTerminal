# MessxTerminal Web

A web-based terminal-style chat application built with Firebase and deployed on Render.

## Features

- Terminal-style interface
- Group chat functionality
- Real-time messaging
- Command support:
  - `@clear` - Clear the screen
  - `@showmess` - Show last 30 messages
  - `@time` - Show current time in UTC, CT, and IST
  - `@help` - Show available commands
  - `@exit` - Log out

## Setup

1. Create a Firebase project:

   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create a new project
   - Enable Firestore Database
   - Set up security rules to allow read/write access

2. Get Firebase configuration:

   - In Firebase Console, go to Project Settings
   - Under "Your apps", click the web icon (</>)
   - Register your app and copy the configuration
   - Create a file named `messxTerminalCreds.json` with the configuration

3. Deploy to Render:
   - Create a new Web Service on Render
   - Connect your repository
   - Set the build command to: `npm install`
   - Set the start command to: `npx serve`
   - Deploy!

## Local Development

1. Install dependencies:

   ```bash
   npm install
   ```

2. Start the development server:

   ```bash
   npx serve
   ```

3. Open `http://localhost:3000` in your browser

## Usage

1. Enter your name when prompted
2. Enter a group name or type 'list' to see existing groups
3. Start chatting!
4. Use commands by typing them with the @ prefix

## Security

- The application uses Firebase's built-in security rules
- Messages are stored in Firestore with timestamps
- No authentication required for simplicity

## License

MIT
