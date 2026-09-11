/**
 * MandiQ — Farmer Feature Phone Simulator & IVR Engine
 * Track 4: Medhavi (Farmer's Phone) · Team RootCause · SIH 2026
 */

(function () {
  'use strict';

  // --- Configuration & Endpoints ---
  const API_BASE = 'http://127.0.0.1:8000/api/v1';
  let isApiOnline = false;

  // --- State Machine ---
  const CallState = {
    IDLE: 'IDLE',
    DIALING: 'DIALING',
    CONNECTED_MENU: 'CONNECTED_MENU',
    BOOKING_CROP: 'BOOKING_CROP',
    BOOKING_CONFIRMED: 'BOOKING_CONFIRMED',
    STATUS_QUERY: 'STATUS_QUERY',
    VOICE_LISTENING: 'VOICE_LISTENING',
    CALL_ENDED: 'CALL_ENDED'
  };

  let currentState = CallState.IDLE;
  let callTimerInterval = null;
  let callSeconds = 0;
  let activeSpeechUtterance = null;
  let speechRecognition = null;
  let isListening = false;

  // Seed Farmer Details for Demo
  const currentFarmer = {
    name: 'रमेश कुमार (Ramesh Kumar)',
    phone: '9876500001',
    village: 'नांगल (Nangal)',
    crop: 'गेहूँ (Wheat)',
    token: 'T-104',
    slotTime: 'कल सुबह 10:00 AM'
  };

  // --- UI Selectors ---
  const lcdTitle = document.getElementById('lcd-call-status');
  const lcdHindi = document.getElementById('lcd-hindi-text');
  const lcdPrompt = document.getElementById('lcd-prompt-state');
  const lcdTimer = document.getElementById('lcd-call-timer');
  const lcdClock = document.getElementById('lcd-clock');
  const btnCallStart = document.getElementById('btn-call-start');
  const btnCallEnd = document.getElementById('btn-call-end');
  const btnMic = document.getElementById('btn-mic');
  const micLabel = document.getElementById('mic-label');
  const smsInboxList = document.getElementById('sms-inbox-list');
  const smsCounter = document.getElementById('sms-counter');
  const consoleLogs = document.getElementById('console-logs');
  const apiStatusText = document.getElementById('api-status-text');
  const apiStatusBadge = document.getElementById('api-status-badge');
  const audioStateBadge = document.getElementById('audio-state');

  // --- Web Audio DTMF & Sound Synthesis ---
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  let audioCtx = null;

  function initAudio() {
    if (!audioCtx) {
      audioCtx = new AudioContext();
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
  }

  // DTMF Frequencies (Hz)
  const dtmfFreqs = {
    '1': [697, 1209], '2': [697, 1336], '3': [697, 1477],
    '4': [770, 1209], '5': [770, 1336], '6': [770, 1477],
    '7': [852, 1209], '8': [852, 1336], '9': [852, 1477],
    '*': [941, 1209], '0': [941, 1336], '#': [941, 1477]
  };

  function playDtmfTone(key) {
    try {
      initAudio();
      const freqs = dtmfFreqs[key];
      if (!freqs) return;

      const osc1 = audioCtx.createOscillator();
      const osc2 = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();

      osc1.frequency.value = freqs[0];
      osc2.frequency.value = freqs[1];

      gainNode.gain.setValueAtTime(0.12, audioCtx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.18);

      osc1.connect(gainNode);
      osc2.connect(gainNode);
      gainNode.connect(audioCtx.destination);

      osc1.start();
      osc2.start();
      osc1.stop(audioCtx.currentTime + 0.18);
      osc2.stop(audioCtx.currentTime + 0.18);
    } catch (e) {
      console.warn('Audio synthesis error:', e);
    }
  }

  function playSmsBeep() {
    try {
      initAudio();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, audioCtx.currentTime);
      osc.frequency.setValueAtTime(1200, audioCtx.currentTime + 0.1);

      gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.35);

      osc.connect(gain);
      gain.connect(audioCtx.destination);

      osc.start();
      osc.stop(audioCtx.currentTime + 0.35);
    } catch (e) {
      console.warn('SMS beep error:', e);
    }
  }

  // --- Clock Updater ---
  function updateClock() {
    const now = new Date();
    let hours = now.getHours();
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12 || 12;
    lcdClock.textContent = `${hours}:${minutes} ${ampm}`;
  }
  setInterval(updateClock, 1000);
  updateClock();

  // --- Logging Console ---
  function logEvent(type, message) {
    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0];
    const div = document.createElement('div');
    div.className = 'log-entry';

    let classColor = 'log-ivr';
    if (type === 'USER') classColor = 'log-user';
    if (type === 'API') classColor = 'log-api';
    if (type === 'WARN') classColor = 'log-warn';

    div.innerHTML = `<span class="log-time">[${timeStr}]</span> <strong class="${classColor}">${type}:</strong> ${message}`;
    consoleLogs.appendChild(div);
    consoleLogs.scrollTop = consoleLogs.scrollHeight;
  }

  // --- Hindi Speech Synthesis (Text to Speech) ---
  function speakHindi(text, onComplete) {
    if (!('speechSynthesis' in window)) {
      logEvent('WARN', 'ब्राउज़र में टेक्स्ट-टू-स्पीच उपलब्ध नहीं है');
      if (onComplete) onComplete();
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'hi-IN';
    utterance.rate = 0.95; // Clear natural pacing for farmers
    utterance.pitch = 1.0;

    // Pick Hindi voice if available
    const voices = window.speechSynthesis.getVoices();
    const hindiVoice = voices.find(v => v.lang.includes('hi') || v.name.includes('Hindi') || v.name.includes('India'));
    if (hindiVoice) {
      utterance.voice = hindiVoice;
    }

    audioStateBadge.textContent = '🔊 बोल रहा है...';

    utterance.onend = () => {
      audioStateBadge.textContent = 'स्पीच तैयार';
      if (onComplete) onComplete();
    };

    utterance.onerror = () => {
      audioStateBadge.textContent = 'स्पीच तैयार';
      if (onComplete) onComplete();
    };

    activeSpeechUtterance = utterance;
    window.speechSynthesis.speak(utterance);
    logEvent('IVR', text);
  }

  // --- Hindi Speech Recognition (Speech to Text) ---
  function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      logEvent('WARN', 'Web Speech Recognition इस ब्राउज़र में समर्थित नहीं है (कीपैड फॉलबैक सक्रिय)');
      return;
    }

    speechRecognition = new SpeechRecognition();
    speechRecognition.lang = 'hi-IN';
    speechRecognition.continuous = false;
    speechRecognition.interimResults = false;

    speechRecognition.onstart = () => {
      isListening = true;
      btnMic.classList.add('listening');
      micLabel.textContent = 'सुन रहे हैं';
      lcdTitle.textContent = 'माइक्रोफोन सक्रिय';
      lcdHindi.textContent = 'सुन रहे हैं... बोलिए';
      lcdPrompt.textContent = '[गाँव / फसल का नाम]';
      audioStateBadge.textContent = '🎙️ सुन रहे हैं...';
      logEvent('USER', 'किसान बोलना शुरू कर रहा है...');
    };

    speechRecognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      logEvent('USER', `सुना गया: "${transcript}"`);
      handleVoiceTranscript(transcript);
    };

    speechRecognition.onerror = (event) => {
      logEvent('WARN', `वाक् पहचान त्रुटि: ${event.error} (कीपैड का उपयोग करें)`);
      stopListening();
      if (currentState === CallState.VOICE_LISTENING) {
        showMenuState();
      }
    };

    speechRecognition.onend = () => {
      stopListening();
    };
  }

  function startListening() {
    if (speechRecognition) {
      try {
        window.speechSynthesis.cancel();
        speechRecognition.start();
      } catch (e) {
        console.warn('Speech recognition start error:', e);
      }
    } else {
      // Fallback simulation if speech recognition is unsupported
      simulateVoiceBooking();
    }
  }

  function stopListening() {
    isListening = false;
    btnMic.classList.remove('listening');
    micLabel.textContent = 'बोलें';
    audioStateBadge.textContent = 'स्पीच तैयार';
  }

  function handleVoiceTranscript(transcript) {
    stopListening();
    lcdHindi.textContent = `प्रोसेसिंग: ${transcript}`;

    // Send to backend voice endpoint
    if (isApiOnline) {
      fetch(`${API_BASE}/voice/inbound`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: currentFarmer.phone,
          transcript: transcript,
          timestamp: new Date().toISOString()
        })
      })
      .then(res => res.json())
      .then(data => {
        logEvent('API', `Voice API Response: ${JSON.stringify(data.message || 'OK')}`);
      })
      .catch(err => console.warn('Voice API error:', err));
    }

    // Process Booking automatically
    setTimeout(() => {
      executeSlotBooking('गेहूँ (Wheat)');
    }, 900);
  }

  // --- Backend API Connectivity Check ---
  async function checkBackendHealth() {
    try {
      const res = await fetch('http://127.0.0.1:8000/health', { method: 'GET', cache: 'no-cache' });
      if (res.ok) {
        isApiOnline = true;
        apiStatusText.textContent = 'सर्वर: कनेक्टेड (8000)';
        apiStatusBadge.style.borderColor = 'rgba(34, 197, 94, 0.4)';
        return;
      }
    } catch (e) {
      // Backend not running or blocked
    }
    isApiOnline = false;
    apiStatusText.textContent = 'मोड: स्टैंडअलोन डेमो';
    apiStatusBadge.style.borderColor = 'rgba(245, 158, 11, 0.4)';
  }
  checkBackendHealth();
  setInterval(checkBackendHealth, 10000);

  // --- Call Flow State Machine Functions ---

  function startCall() {
    initAudio();
    if (currentState !== CallState.IDLE && currentState !== CallState.CALL_ENDED) {
      return;
    }

    currentState = CallState.DIALING;
    lcdTitle.textContent = 'डायल हो रहा है...';
    lcdHindi.textContent = '1800-202-0019 (टोल-फ्री)';
    lcdPrompt.textContent = 'मंडी-क्यू सर्वर से कनेक्टिंग...';
    lcdTimer.style.display = 'none';

    logEvent('USER', 'टोल-फ्री 1800-202-0019 पर कॉल लगाया गया');

    // Simulate ring and connect
    setTimeout(() => {
      connectCall();
    }, 1200);
  }

  function connectCall() {
    currentState = CallState.CONNECTED_MENU;
    callSeconds = 0;
    lcdTimer.style.display = 'block';
    lcdTimer.textContent = '00:00';

    clearInterval(callTimerInterval);
    callTimerInterval = setInterval(() => {
      callSeconds++;
      const mins = String(Math.floor(callSeconds / 60)).padStart(2, '0');
      const secs = String(callSeconds % 60).padStart(2, '0');
      lcdTimer.textContent = `${mins}:${secs}`;
    }, 1000);

    showMenuState();
  }

  function showMenuState() {
    currentState = CallState.CONNECTED_MENU;
    lcdTitle.textContent = 'मंडी-क्यू IVR';
    lcdHindi.textContent = 'नया स्लॉट: 1 दबाएँ | स्थिति: 2 दबाएँ';
    lcdPrompt.textContent = '[ अथवा माइक बटन दबाकर बोलें ]';

    const promptSpeech = 'मंडी-क्यू में आपका स्वागत है। स्लॉट बुक करना है, तो एक दबाइए। अपनी कतार स्थिति जानने के लिए, दो दबाइए। अथवा माइक दबाकर बोलिए।';
    speakHindi(promptSpeech);
  }

  function endCall() {
    window.speechSynthesis.cancel();
    stopListening();
    clearInterval(callTimerInterval);

    currentState = CallState.CALL_ENDED;
    lcdTitle.textContent = 'कॉल समाप्त';
    lcdHindi.textContent = 'कॉल कट गई है। धन्यवाद!';
    lcdPrompt.textContent = '[ पुनः कॉल हेतु हरा बटन दबाएँ ]';
    lcdTimer.style.display = 'none';

    logEvent('USER', 'कॉल समाप्त की गई');

    setTimeout(() => {
      currentState = CallState.IDLE;
      lcdTitle.textContent = 'मंडी-क्यू सेवा';
      lcdHindi.textContent = 'कॉल करने के लिए हरा बटन दबाएँ';
      lcdPrompt.textContent = '[ 1: बुक | 2: स्थिति ]';
    }, 2800);
  }

  // Keypad DTMF Input Handling
  function handleKeyPress(key) {
    playDtmfTone(key);
    logEvent('USER', `कीपैड दबाया: ${key}`);

    if (currentState === CallState.IDLE) {
      // Direct call on pressing 1 or 2 from standby
      if (key === '1' || key === '2') {
        startCall();
        setTimeout(() => {
          handleKeyPress(key);
        }, 1600);
      }
      return;
    }

    if (currentState === CallState.CONNECTED_MENU) {
      if (key === '1') {
        promptCropSelection();
      } else if (key === '2') {
        executeStatusCheck();
      } else if (key === '*') {
        showMenuState();
      }
      return;
    }

    if (currentState === CallState.BOOKING_CROP) {
      let selectedCrop = 'गेहूँ (Wheat)';
      if (key === '3') selectedCrop = 'गेहूँ (Wheat)';
      else if (key === '4') selectedCrop = 'धान (Paddy)';
      else if (key === '5') selectedCrop = 'सरसों (Mustard)';
      else if (key === '6') selectedCrop = 'मक्का (Maize)';
      else {
        selectedCrop = 'गेहूँ (Wheat)';
      }
      executeSlotBooking(selectedCrop);
      return;
    }

    if (currentState === CallState.BOOKING_CONFIRMED || currentState === CallState.STATUS_QUERY) {
      if (key === '*') {
        showMenuState();
      } else if (key === '#') {
        endCall();
      }
    }
  }

  // Crop Selection Step
  function promptCropSelection() {
    currentState = CallState.BOOKING_CROP;
    lcdTitle.textContent = 'फसल चयन';
    lcdHindi.textContent = 'गेहूँ: 3 | धान: 4 | सरसों: 5';
    lcdPrompt.textContent = '[ फसल संख्या चुनें या नाम बोलें ]';

    const speech = 'कृपया फसल चुनें। गेहूँ के लिए तीन, धान के लिए चार, सरसों के लिए पाँच दबाइए।';
    speakHindi(speech);
  }

  // Execute Slot Booking
  async function executeSlotBooking(cropName) {
    currentState = CallState.BOOKING_CONFIRMED;
    lcdTitle.textContent = 'बुकिंग सफल!';
    lcdHindi.textContent = `टोकन: ${currentFarmer.token} | ${currentFarmer.slotTime}`;
    lcdPrompt.textContent = `फसल: ${cropName} · करनाल मंडी`;

    logEvent('API', `स्लॉट आरक्षित किया गया -> टोकन: ${currentFarmer.token}`);

    // Call live API if online
    if (isApiOnline) {
      try {
        const response = await fetch(`${API_BASE}/bookings/book-slot`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            phone: currentFarmer.phone,
            crop: cropName,
            village: currentFarmer.village
          })
        });
        const resData = await response.json();
        logEvent('API', `सर्वर पुष्टि: ${JSON.stringify(resData.message || 'Booked')}`);
      } catch (e) {
        logEvent('WARN', 'स्थानीय सिम्युलेशन मोड में बुकिंग जारी');
      }
    }

    // Spoken Hindi Confirmation
    const confirmSpeech = `बधाई हो! आपका टोकन नंबर ${currentFarmer.token} है। करनाल मंडी में आपका समय ${currentFarmer.slotTime} निर्धारित हुआ है। आपके फोन पर एसएमएस भेज दिया गया है।`;
    speakHindi(confirmSpeech);

    // Send SMS to Farmer's Inbox
    deliverSms({
      sender: 'VK-MANDIQ',
      body: `MandiQ: प्रिय ${currentFarmer.name}, आपका टोकन ${currentFarmer.token} है। करनाल मंडी स्लॉट: ${currentFarmer.slotTime}। फसल: ${cropName}। कृपया समय पर ट्रैक्टर लेकर पहुँचें।`,
      token: currentFarmer.token,
      isAlert: false
    });
  }

  // Execute Status Check (Key 2)
  async function executeStatusCheck() {
    currentState = CallState.STATUS_QUERY;
    lcdTitle.textContent = 'कतार स्थिति';
    lcdHindi.textContent = 'टोकन: T-101 | आगे: 3 ट्रैक्टर';
    lcdPrompt.textContent = 'अनुमानित प्रतीक्षा: 20 मिनट';

    logEvent('API', `कतार जांच -> टोकन T-101`);

    if (isApiOnline) {
      try {
        const response = await fetch(`${API_BASE}/queue/T-101`, { method: 'GET' });
        const data = await response.json();
        logEvent('API', `Queue API: ${JSON.stringify(data)}`);
      } catch (e) {
        logEvent('WARN', 'स्थानीय सिम्युलेशन से कतार स्थिति प्रदर्शित');
      }
    }

    const statusSpeech = 'आपका टोकन नंबर टी एक सौ एक है। वर्तमान में टोकन अठानवे चल रहा है। आपकी बारी आने में लगभग बीस मिनट लगेंगे।';
    speakHindi(statusSpeech);

    deliverSms({
      sender: 'VK-MANDIQ',
      body: `MandiQ STATUS: आपका टोकन T-101 है। वर्तमान टोकन T-98 चल रहा है। अनुमानित समय 20 मिनट शेष। करनाल गेट नं 2 पर संपर्क करें।`,
      token: 'T-101',
      isAlert: false
    });
  }

  // --- SMS Delivery System ---
  let smsCount = 1;
  function deliverSms({ sender, body, token, isAlert = false }) {
    playSmsBeep();
    smsCount++;
    smsCounter.textContent = `${smsCount} संदेश`;

    const now = new Date();
    const timeStr = `${now.getHours() % 12 || 12}:${String(now.getMinutes()).padStart(2, '0')} ${now.getHours() >= 12 ? 'PM' : 'AM'}`;

    const bubble = document.createElement('div');
    bubble.className = `sms-bubble new ${isAlert ? 'alert' : ''}`;
    bubble.innerHTML = `
      <div class="sms-header">
        <span class="sms-sender">${sender}</span>
        <span class="sms-time">${timeStr}</span>
      </div>
      <div class="sms-body">${body}</div>
      ${token ? `<span class="sms-token-tag">टोकन: ${token}</span>` : ''}
    `;

    smsInboxList.insertBefore(bubble, smsInboxList.firstChild);
    logEvent('API', `किसान फोन पर SMS प्राप्त: "${body.substring(0, 42)}..."`);
  }

  // --- 4-Minute Demo Pitch Scenarios for Judges ---

  // 1. Voice Booking Demo (0:20 - 1:30 in Demo Plan)
  function simulateVoiceBooking() {
    startCall();
    setTimeout(() => {
      lcdTitle.textContent = 'वॉइस बुकिंग';
      lcdHindi.textContent = '"रमेश कुमार, नांगल, गेहूँ"';
      lcdPrompt.textContent = 'पहचाना गया... टोकन बन रहा है';
      logEvent('USER', 'किसान बोला: "मेरा गाँव नांगल है, फसल गेहूँ है, स्लॉट बुक करें"');
      
      setTimeout(() => {
        executeSlotBooking('गेहूँ (Wheat)');
      }, 1500);
    }, 2000);
  }

  // 2. Status Check Demo
  function simulateStatusCheck() {
    startCall();
    setTimeout(() => {
      handleKeyPress('2');
    }, 2000);
  }

  // 3. Mandi HALT Demo (2:00 - 3:00 Demo Moment)
  function simulateHaltAlert() {
    logEvent('WARN', '🔴 मंडी स्टाफ ने HALT PROCUREMENT बटन दबाया!');
    
    // Simulate HALT notice on screen if in call, or deliver urgent SMS
    deliverSms({
      sender: 'VK-MANDIQ-HALT',
      body: `🔴 आवश्यक सूचना: करनाल मंडी में शेड की तकनीकी खराबी के कारण आज का कार्य रोक दिया गया है। प्रिय रमेश कुमार, आपका नया स्लॉट परसों 10:00 AM कर दिया गया है। आपका नया टोकन: T-204। पुरानी पर्ची मान्य नहीं होगी।`,
      token: 'T-204',
      isAlert: true
    });

    lcdTitle.textContent = '🔴 मंडी रुकावट SMS';
    lcdHindi.textContent = 'नया टोकन: T-204 | परसों 10 AM';
    lcdPrompt.textContent = '[ स्वतः पुनर्निर्धारण (Auto-Reschedule) ]';

    const haltSpeech = 'ध्यान दें किसान भाई! मंडी में कार्य रुकने के कारण आपका स्लॉट परसों सुबह दस बजे के लिए पुनर्निर्धारित कर दिया गया है। आपका नया टोकन टी दो सौ चार है।';
    speakHindi(haltSpeech);
  }

  // 4. Reset Simulator
  function resetSimulator() {
    window.speechSynthesis.cancel();
    stopListening();
    clearInterval(callTimerInterval);
    currentState = CallState.IDLE;
    lcdTitle.textContent = 'मंडी-क्यू सेवा';
    lcdHindi.textContent = 'कॉल करने के लिए हरा बटन दबाएँ';
    lcdPrompt.textContent = '[ 1: बुक | 2: स्थिति ]';
    lcdTimer.style.display = 'none';
    logEvent('IVR', 'सिम्युलेटर रीसेट किया गया');
  }

  // --- Event Listeners Attachment ---

  // Keypad click listeners
  document.querySelectorAll('.key-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.getAttribute('data-key');
      handleKeyPress(key);
    });
  });

  // Call start & end buttons
  btnCallStart.addEventListener('click', () => {
    startCall();
  });

  btnCallEnd.addEventListener('click', () => {
    endCall();
  });

  // Microphone toggle button
  btnMic.addEventListener('click', () => {
    initAudio();
    if (isListening) {
      stopListening();
    } else {
      if (currentState === CallState.IDLE) {
        startCall();
        setTimeout(() => {
          currentState = CallState.VOICE_LISTENING;
          startListening();
        }, 1500);
      } else {
        currentState = CallState.VOICE_LISTENING;
        startListening();
      }
    }
  });

  // Softkeys
  document.getElementById('btn-soft-left').addEventListener('click', () => {
    playDtmfTone('1');
    if (currentState === CallState.CONNECTED_MENU) {
      promptCropSelection();
    } else {
      startCall();
    }
  });

  document.getElementById('btn-soft-right').addEventListener('click', () => {
    playDtmfTone('#');
    endCall();
  });

  // Demo Trigger Buttons
  document.getElementById('demo-voice-booking').addEventListener('click', simulateVoiceBooking);
  document.getElementById('demo-status-check').addEventListener('click', simulateStatusCheck);
  document.getElementById('demo-halt-sms').addEventListener('click', simulateHaltAlert);
  document.getElementById('demo-clear-all').addEventListener('click', resetSimulator);

  // Keyboard physical listener (1-9, *, #, Enter for Call, Esc for End)
  window.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (dtmfFreqs[e.key]) {
      handleKeyPress(e.key);
    } else if (e.key === 'Enter') {
      startCall();
    } else if (e.key === 'Escape') {
      endCall();
    }
  });

  // Initialize Speech Recognition on load
  setupSpeechRecognition();

  logEvent('IVR', 'सिम्युलेटर तैयार। किसान फोन इंटरफ़ेस लोड हो गया है।');

})();
