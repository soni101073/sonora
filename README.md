# Implementing Lock Screen Media Controls (Media Session API)

If you are building a web-based media player (like a podcast app, music player, or custom audio streamer) and want it to feel like a native iOS or Android app, you need to use the **Media Session API**.

This API allows your web app to display rich metadata (title, artist, and album art) on the device's lock screen, smartwatches, and control centers. It also lets you intercept the physical media keys and lock screen buttons (play, pause, skip).

## 1. Prerequisites
- You must be using native HTML5 `<audio>` or `<video>` tags.
- Background playback on iOS requires the media to be started via a **direct user interaction** (e.g., a tap or click).
- (Optional but recommended) Your web app should ideally be served over HTTPS.

## 2. Setting Media Metadata

Whenever a new track or episode starts playing, update the `navigator.mediaSession.metadata` object. This tells the OS what image and text to put on the lock screen.

```javascript
function updateLockScreenMetadata(trackTitle, artistName, imageUrl) {
  if ('mediaSession' in navigator) {
    navigator.mediaSession.metadata = new MediaMetadata({
      title: trackTitle,
      artist: artistName,
      album: 'My Awesome App', // Optional
      artwork: [
        { src: imageUrl, sizes: '96x96', type: 'image/jpeg' },
        { src: imageUrl, sizes: '128x128', type: 'image/jpeg' },
        { src: imageUrl, sizes: '192x192', type: 'image/jpeg' },
        { src: imageUrl, sizes: '256x256', type: 'image/jpeg' },
        { src: imageUrl, sizes: '384x384', type: 'image/jpeg' },
        { src: imageUrl, sizes: '512x512', type: 'image/jpeg' }
      ]
    });
  }
}
```

*Tip: Providing multiple artwork sizes ensures it looks crisp on everything from an Apple Watch to a 4K desktop monitor.*

## 3. Handling Lock Screen Actions

Next, you need to map the physical OS buttons back to your JavaScript audio controls. If you don't do this, the lock screen buttons might be grayed out or do nothing.

```javascript
// Assuming you have an HTML5 audio element: const audio = new Audio();

if ('mediaSession' in navigator) {
  
  // Play button on lock screen or headphones
  navigator.mediaSession.setActionHandler('play', () => {
    audio.play();
  });

  // Pause button
  navigator.mediaSession.setActionHandler('pause', () => {
    audio.pause();
  });

  // Skip Forward (e.g. 15 seconds)
  navigator.mediaSession.setActionHandler('seekforward', () => {
    audio.currentTime = Math.min(audio.currentTime + 15, audio.duration);
  });

  // Skip Backward (e.g. 15 seconds)
  navigator.mediaSession.setActionHandler('seekbackward', () => {
    audio.currentTime = Math.max(audio.currentTime - 15, 0);
  });

  // Next Track (for playlists)
  navigator.mediaSession.setActionHandler('nexttrack', () => {
    playNextSongInPlaylist();
  });

  // Previous Track
  navigator.mediaSession.setActionHandler('previoustrack', () => {
    playPreviousSongInPlaylist();
  });
}
```

## 4. Syncing the OS Progress Bar (Position State)

To make the scrubbing bar on the lock screen accurately reflect the audio's timeline, you can update the position state. Call this whenever the track loads or when the user seeks.

```javascript
function updatePositionState(audioElement) {
  if ('mediaSession' in navigator && 'setPositionState' in navigator.mediaSession) {
    if (audioElement.duration && !isNaN(audioElement.duration)) {
      navigator.mediaSession.setPositionState({
        duration: audioElement.duration,
        playbackRate: audioElement.playbackRate,
        position: audioElement.currentTime
      });
    }
  }
}

// Example: Call it when metadata loads or the user drags your custom scrub bar
// audio.addEventListener('loadedmetadata', () => updatePositionState(audio));
```

## Summary Checklist
1. Ensure media originates from `<audio>`/`<video>`.
2. Wrap your `mediaSession` code in an `if ('mediaSession' in navigator)` check to avoid crashing older browsers.
3. Update `MediaMetadata` with title, artist, and images when the song changes.
4. Bind `setActionHandler` for `play`, `pause`, and seeking logic.