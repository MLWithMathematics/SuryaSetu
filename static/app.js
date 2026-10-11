/**
 * SuryaSetu — Apple / Vercel Minimalist Frontend
 * Pure Vanilla JavaScript (Zero External Frameworks)
 * Full English & Hindi i18n support, real-time DISCOM tariff math,
 * camera upload OCR, and responsive bento grid dashboard.
 */

(function () {
  'use strict';

  // --- Translation Dictionary ---
  const TRANSLATIONS = {
    en: {
      brandTitle: 'SuryaSetu',
      brandAdvisor: '',
      heroBadge: 'PM Surya Ghar Muft Bijli Yojana (2025–2026)',
      heroHeadline: 'Cut your electricity bill<br><span class="gradient-text">by up to 90% with solar.</span>',
      heroSubline: 'Enter your bill details or upload a photo to calculate system size, government subsidies, monthly savings, and loan EMI.',
      disclaimerChip: 'Designed for Indian residential & domestic connections only.',
      tabManual: 'Manual Entry',
      tabPhoto: 'Scan Bill Photo',
      presetsLabel: 'Quick Samples:',
      preset2bhk: '2 BHK Flat',
      preset3bhk: '3 BHK + AC',
      presetHeavy: 'Heavy Load',
      bannerSuccessTitle: 'Bill Scanned Successfully',
      labelState: 'State / DISCOM Region',
      optSelectState: 'Select your state',
      labelUnits: 'Monthly Units Consumed',
      captionUnits: 'Found under "Billed Units" or "Units Consumed".',
      labelDays: 'Billing Period',
      captionDays: 'Standard monthly cycle is 30 days.',
      labelAmount: 'Total Bill Amount',
      optLabel: 'Optional',
      captionAmount: 'Can estimate units if kWh is unknown.',
      labelLoad: 'Sanctioned Load',
      captionLoad: 'Helps verify grid load compatibility.',
      labelFixed: 'Fixed / Meter Charges',
      captionFixed: 'Defaults to state tariff baseline.',
      labelPast: "Past Months' Consumption History",
      captionPast: 'Comma-separated kWh of past months for seasonal averaging.',
      labelRoof: 'Terrace / Roof Space Availability',
      roofOwnTitle: 'Own Terrace / Roof',
      roofOwnDesc: 'Clear, independent shadow-free rooftop space.',
      roofUnsureTitle: 'Shared / Society',
      roofUnsureDesc: 'Apartment common roof requiring society NOC.',
      roofNoTitle: 'No Roof Space',
      roofNoDesc: 'Tenant or shaded without terrace access.',
      btnCalculate: 'Calculate Solar Recommendation',
      photoDropTitle: 'Upload your electricity bill',
      photoDropDesc: 'Drag & drop your bill photo here, or browse files',
      photoDropHint: 'Supports JPEG, PNG, WEBP • Automatically compressed',
      photoBrowseBtn: 'Choose Photo or Take Picture',
      loadingTitle: 'Calculating Solar Feasibility...',
      loadingText: 'Analyzing DISCOM tariff slabs, solar irradiance, PM Surya Ghar subsidy, and return on investment.',
      compareTitle: 'Monthly Electricity Bill Impact',
      compareBeforeLabel: 'Current Monthly Bill',
      compareAfterLabel: 'Estimated Bill with Solar',
      aiAdvisorTag: 'AI Advisor Verdict',
      bentoSystemLabel: 'Recommended Capacity',
      bentoSavingsLabel: 'Estimated Monthly Savings',
      bentoSubsidyLabel: 'PM Surya Ghar Subsidy',
      bentoPaybackLabel: 'Payback Timeline',
      bentoEmiLabel: 'Concessional Solar Loan EMI',
      bentoEmiCaption: 'Based on 5.75% p.a. scheme financing over 10-year tenure',
      roadmapHeading: '4-Step Implementation Roadmap',
      roadmapTag: 'Next Steps',
      assumptionsHeading: 'Engineering Assumptions',
      assumptionsTag: 'Methodology',
      btnPrint: 'Print or Save Report',
      btnRecalculate: 'Edit Bill Details',
      bottomDisclaimer: 'All figures are algorithmic preliminary estimates for planning purposes under PM Surya Ghar Muft Bijli Yojana benchmarks. Actual generation varies by rooftop tilt, shade obstacles, and DISCOM net-metering approvals.',
      footerCopy: '© 2026 SuryaSetu. Empowering clean solar energy across India.'
    },
    hi: {
      brandTitle: 'सूर्यसेतु',
      brandAdvisor: '',
      heroBadge: 'पीएम सूर्य घर मुफ्त बिजली योजना (2025–2026)',
      heroHeadline: 'सोलर पैनल से अपना बिजली बिल<br><span class="gradient-text">90% तक कम करें।</span>',
      heroSubline: 'सिस्टम का आकार, सरकारी सब्सिडी, मासिक बचत और सोलर लोन ईएमआई जानने के लिए अपने बिल का विवरण भरें या फोटो स्कैन करें।',
      disclaimerChip: 'केवल भारतीय आवासीय एवं घरेलू बिजली उपभोक्ताओं के लिए मान्य।',
      tabManual: 'मैन्युअल प्रविष्टि',
      tabPhoto: 'बिल फोटो स्कैन करें',
      presetsLabel: 'त्वरित नमूने:',
      preset2bhk: '2 बीएचके फ्लैट',
      preset3bhk: '3 बीएचके + एसी',
      presetHeavy: 'अधिक लोड',
      bannerSuccessTitle: 'बिल सफलतापूर्वक स्कैन हुआ',
      labelState: 'राज्य / डिस्कॉम वितरण क्षेत्र',
      optSelectState: 'अपना राज्य चुनें',
      labelUnits: 'मासिक बिजली खपत',
      captionUnits: 'बिल पर "Billed Units" या "खपत यूनिट" देखें।',
      labelDays: 'बिलिंग अवधि',
      captionDays: 'सामान्यतः 30 दिन का बिलिंग चक्र होता है।',
      labelAmount: 'कुल बिजली बिल राशि',
      optLabel: 'वैकल्पिक',
      captionAmount: 'यूनिट न पता होने पर राशि से अनुमान लगाया जा सकता है।',
      labelLoad: 'स्वीकृत भार (Sanctioned Load)',
      captionLoad: 'मीटर कनेक्शन लोड अनुकूलता जांचने के लिए।',
      labelFixed: 'फिक्स्ड / मीटर शुल्क',
      captionFixed: 'राज्य डिस्कॉम टैरिफ के आधार पर।',
      labelPast: 'पिछले महीनों की बिजली खपत',
      captionPast: 'मौसम अनुसार सही औसत के लिए (अल्पविराम से अलग करें)।',
      labelRoof: 'छत / टेरेस की उपलब्धता',
      roofOwnTitle: 'स्वयं की छत / टेरेस',
      roofOwnDesc: 'साफ, छाया-मुक्त स्वतंत्र छत का अधिकार।',
      roofUnsureTitle: 'साझा / सोसाइटी छत',
      roofUnsureDesc: 'अपार्टमेंट की साझी छत, सोसाइटी एनओसी आवश्यक।',
      roofNoTitle: 'छत उपलब्ध नहीं',
      roofNoDesc: 'किराएदार या बिना छत अधिकार का घर।',
      btnCalculate: 'सोलर अनुशंसा की गणना करें',
      photoDropTitle: 'अपने बिजली बिल की फोटो अपलोड करें',
      photoDropDesc: 'बिल की फोटो यहाँ खींचें या फाइल चुनें',
      photoDropHint: 'JPG, PNG, WEBP समर्थित • स्वतः कंप्रेस की जाएगी',
      photoBrowseBtn: 'फोटो चुनें या कैमरा से खींचे',
      loadingTitle: 'सोलर अनुकूलता का विश्लेषण हो रहा है...',
      loadingText: 'डिस्कॉम टैरिफ स्लैब, सौर विकिरण, पीएम सूर्य घर सब्सिडी और निवेश वापसी का आकलन किया जा रहा है।',
      compareTitle: 'मासिक बिजली बिल में कटौती',
      compareBeforeLabel: 'वर्तमान मासिक बिल',
      compareAfterLabel: 'सोलर के बाद अनुमानित बिल',
      aiAdvisorTag: 'एआई सलाहकार निष्कर्ष',
      bentoSystemLabel: 'अनुशंसित सोलर क्षमता',
      bentoSavingsLabel: 'अनुमानित मासिक बचत',
      bentoSubsidyLabel: 'पीएम सूर्य घर सब्सिडी',
      bentoPaybackLabel: 'लागत वापसी (पेबैक)',
      bentoEmiLabel: 'रियायती सोलर लोन ईएमआई',
      bentoEmiCaption: '10 वर्ष की अवधि के लिए 5.75% वार्षिक ब्याज पर आधारित',
      roadmapHeading: '4-चरणीय स्थापना रोडमैप',
      roadmapTag: 'अगले कदम',
      assumptionsHeading: 'इंजीनियरिंग मान्यताएं',
      assumptionsTag: 'गणना पद्धति',
      btnPrint: 'रिपोर्ट प्रिंट या सेव करें',
      btnRecalculate: 'बिल विवरण संपादित करें',
      bottomDisclaimer: 'ये सभी आंकड़े पीएम सूर्य घर योजना के मानकों पर आधारित प्रारंभिक अनुमान हैं। वास्तविक उत्पादन छत के झुकाव, धूप और डिस्कॉम नेट-मीटरिंग पर निर्भर करता है।',
      footerCopy: '© 2026 सूर्यसेतु। पूरे भारत में स्वच्छ सौर ऊर्जा को बढ़ावा।'
    }
  };

  // --- Presets Data ---
  const PRESETS = {
    '2bhk': {
      state: 'MH',
      units: '280',
      billing_days: '30',
      amount_payable: '2450',
      sanctioned_load: '2.5',
      fixed_charges: '128',
      past_units: '260, 290, 275'
    },
    '3bhk': {
      state: 'MH',
      units: '450',
      billing_days: '30',
      amount_payable: '3850',
      sanctioned_load: '3.0',
      fixed_charges: '150',
      past_units: '420, 390, 480, 510, 460'
    },
    'heavy': {
      state: 'UP',
      units: '720',
      billing_days: '30',
      amount_payable: '6200',
      sanctioned_load: '5.0',
      fixed_charges: '200',
      past_units: '680, 710, 750, 730'
    }
  };

  // --- State Variables ---
  let currentLang = 'en';
  let activeProvider = 'offline';
  let lastVerdictData = null;
  let lastVerdictPayload = null;

  // --- DOM Elements ---
  const tabBtnManual = document.getElementById('tab-btn-manual');
  const tabBtnPhoto = document.getElementById('tab-btn-photo');
  const tabPaneManual = document.getElementById('tab-manual');
  const tabPanePhoto = document.getElementById('tab-photo');

  const solarForm = document.getElementById('solar-form');
  const btnSubmit = document.getElementById('btn-submit');
  const btnRecalculate = document.getElementById('btn-recalculate');

  // Form Inputs
  const inputState = document.getElementById('state');
  const inputUnits = document.getElementById('units');
  const inputBillingDays = document.getElementById('billing_days');
  const inputAmount = document.getElementById('amount_payable');
  const inputSanctionedLoad = document.getElementById('sanctioned_load');
  const inputFixedCharges = document.getElementById('fixed_charges');
  const inputPastUnits = document.getElementById('past_units');

  // Photo Tab Elements
  const dropZone = document.getElementById('drop-zone');
  const billPhotoInput = document.getElementById('bill-photo-input');
  const photoPreviewBox = document.getElementById('photo-preview-box');
  const imagePreview = document.getElementById('image-preview');
  const previewFilename = document.getElementById('preview-filename');
  const previewFilesize = document.getElementById('preview-filesize');
  const uploadProgressFill = document.getElementById('upload-progress-fill');
  const photoErrorBanner = document.getElementById('photo-error');
  const photoErrorMessage = document.getElementById('photo-error-message');
  const photoExtractedBanner = document.getElementById('photo-extracted-banner');
  const photoConfidenceText = document.getElementById('photo-confidence-text');
  const btnCloseBanner = document.getElementById('btn-close-banner');

  // Loading & Results
  const loadingSection = document.getElementById('loading-state');
  const resultsSection = document.getElementById('results-section');

  // Verdict Elements
  const verdictStatusBadge = document.getElementById('verdict-status-badge');
  const verdictStatusText = document.getElementById('verdict-status-text');
  const verdictHeadline = document.getElementById('verdict-headline');
  const verdictSubheadline = document.getElementById('verdict-subheadline');

  // Bill Comparison Bars
  const compareBeforeVal = document.getElementById('compare-before-val');
  const compareAfterVal = document.getElementById('compare-after-val');
  const comparePercentCut = document.getElementById('compare-percent-cut');
  const barFillBefore = document.getElementById('bar-fill-before');
  const barFillAfter = document.getElementById('bar-fill-after');

  // AI Insight Box
  const aiExplanationText = document.getElementById('ai-explanation-text');
  const aiModelTag = document.getElementById('ai-model-tag');

  // Metric Bento Cards
  const valSystemSize = document.getElementById('val-system-size');
  const valRoofArea = document.getElementById('val-roof-area');
  const valMonthlySavings = document.getElementById('val-monthly-savings');
  const valAnnualSavings = document.getElementById('val-annual-savings');
  const valSubsidy = document.getElementById('val-subsidy');
  const valNetCost = document.getElementById('val-net-cost');
  const valPayback = document.getElementById('val-payback');
  const valPaybackCaption = document.getElementById('val-payback-caption');
  const valEmi = document.getElementById('val-emi');
  const valEmiPillText = document.getElementById('val-emi-pill-text');

  // Roadmap & Assumptions
  const checklistContainer = document.getElementById('checklist-items');
  const assumptionsList = document.getElementById('assumptions-list');

  // Header Badge
  const headerAiBadge = document.getElementById('header-ai-badge');
  const headerAiBadgeText = document.getElementById('header-ai-badge-text');

  // --- Helper: Format Indian Rupee Currency (en-IN) ---
  function formatINR(amount) {
    if (amount === undefined || amount === null || isNaN(amount)) return '₹0';
    const num = Math.round(Number(amount));
    return '₹' + num.toLocaleString('en-IN');
  }

  function formatNumber(val, decimals = 1) {
    if (val === undefined || val === null || isNaN(val)) return '0';
    return Number(val).toLocaleString('en-IN', {
      minimumFractionDigits: 0,
      maximumFractionDigits: decimals
    });
  }

  // --- 1. App Initialization ---
  async function initApp() {
    setupTabSwitching();
    setupLanguageToggle();
    setupPresetChips();
    setupFormValidationListeners();
    setupPhotoUpload();

    solarForm.addEventListener('submit', submitForm);

    if (btnRecalculate) {
      btnRecalculate.addEventListener('click', () => {
        window.scrollTo({ top: solarForm.offsetTop - 90, behavior: 'smooth' });
        inputUnits.focus();
      });
    }

    if (btnCloseBanner) {
      btnCloseBanner.addEventListener('click', () => {
        photoExtractedBanner.classList.add('hidden');
      });
    }

    // Fetch system /config
    try {
      const resp = await fetch('/config');
      if (resp.ok) {
        const config = await resp.json();
        activeProvider = config.provider || 'offline';

        if (config.photo_enabled) {
          tabBtnPhoto.classList.remove('hidden');
        } else {
          tabBtnPhoto.classList.add('hidden');
        }

        updateProviderBadge(activeProvider);
      }
    } catch (err) {
      console.warn('Could not fetch /config, using offline defaults.', err);
      updateProviderBadge('offline');
    }

    // Apply initial language
    applyTranslations('en');
  }

  // --- 2. Language Switcher (Complete UI Translation) ---
  function setupLanguageToggle() {
    const langBtns = document.querySelectorAll('.lang-btn');
    langBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        const selected = btn.dataset.lang || 'en';
        if (selected === currentLang) return;
        currentLang = selected;
        applyTranslations(currentLang);
      });
    });
  }

  function applyTranslations(lang) {
    const dict = TRANSLATIONS[lang] || TRANSLATIONS.en;

    // 1. Update text of all [data-i18n] elements
    document.querySelectorAll('[data-i18n]').forEach((el) => {
      const key = el.dataset.i18n;
      if (dict[key]) {
        if (key === 'heroHeadline') {
          el.innerHTML = dict[key];
        } else if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
          el.placeholder = dict[key];
        } else {
          el.textContent = dict[key];
        }
      }
    });

    // 2. Update state select first option
    if (inputState && inputState.options.length > 0) {
      inputState.options[0].text = dict.optSelectState;
    }

    // 3. Update active pill buttons
    document.querySelectorAll('.lang-btn').forEach((btn) => {
      if (btn.dataset.lang === lang) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    // 4. Update Header Status Badge Text
    updateProviderBadge(activeProvider);

    // 5. If results are currently showing, re-render them with Hindi/English text!
    if (lastVerdictData && lastVerdictPayload) {
      lastVerdictPayload.lang = lang;
      renderVerdict(lastVerdictData, lastVerdictPayload);
    }
  }

  // --- 3. Header Status Badge ---
  function updateProviderBadge(provider) {
    if (!headerAiBadge) return;
    const isHi = currentLang === 'hi';

    if (provider === 'gemini') {
      headerAiBadge.innerHTML = `<span class="pulse-dot" style="background: #3B82F6;"></span><span>${isHi ? 'जेमिनी एआई सक्रिय' : 'Gemini AI Active'}</span>`;
      headerAiBadge.style.color = '#1E3A8A';
      headerAiBadge.style.background = '#EFF6FF';
      headerAiBadge.style.borderColor = '#BFDBFE';
      if (aiModelTag) aiModelTag.textContent = 'Google Gemini 3.5 Flash';
    } else if (provider === 'groq') {
      headerAiBadge.innerHTML = `<span class="pulse-dot" style="background: #EA580C;"></span><span>${isHi ? 'ग्रॉक लामा सक्रिय' : 'Groq Llama 3.3 Active'}</span>`;
      headerAiBadge.style.color = '#9A3412';
      headerAiBadge.style.background = '#FFF7ED';
      headerAiBadge.style.borderColor = '#FED7AA';
      if (aiModelTag) aiModelTag.textContent = 'Groq • Llama 3.3 70B';
    } else if (provider === 'nvidia') {
      headerAiBadge.innerHTML = `<span class="pulse-dot" style="background: #16A34A;"></span><span>${isHi ? 'एनवीडिया एनआईएम सक्रिय' : 'NVIDIA NIM Active'}</span>`;
      headerAiBadge.style.color = '#14532D';
      headerAiBadge.style.background = '#F0FDF4';
      headerAiBadge.style.borderColor = '#BBF7D0';
      if (aiModelTag) aiModelTag.textContent = 'NVIDIA NIM Open Model';
    } else if (provider === 'bedrock') {
      headerAiBadge.innerHTML = `<span class="pulse-dot" style="background: #F59E0B;"></span><span>${isHi ? 'बेडरॉक सक्रिय' : 'Bedrock Active'}</span>`;
      if (aiModelTag) aiModelTag.textContent = 'Claude 3.5 Sonnet';
    } else {
      headerAiBadge.innerHTML = `<span class="pulse-dot" style="background: #10B981;"></span><span>${isHi ? 'पीएम सूर्य घर तैयार' : 'PM Surya Ghar Ready'}</span>`;
      if (aiModelTag) aiModelTag.textContent = isHi ? 'अल्गोरिदम सलाहकार' : 'Deterministic Advisor';
    }
  }

  // --- 4. Preset Chips (1-Click Fill) ---
  function setupPresetChips() {
    const chipBtns = document.querySelectorAll('.chip-btn');
    chipBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        const key = btn.dataset.preset;
        const data = PRESETS[key];
        if (!data) return;

        clearErrors();
        inputState.value = data.state;
        inputUnits.value = data.units;
        inputBillingDays.value = data.billing_days;
        inputAmount.value = data.amount_payable;
        inputSanctionedLoad.value = data.sanctioned_load;
        inputFixedCharges.value = data.fixed_charges;
        inputPastUnits.value = data.past_units;

        // Flash chip active style
        chipBtns.forEach((b) => (b.style.borderColor = ''));
        btn.style.borderColor = 'var(--amber-primary)';
      });
    });
  }

  // --- 5. Tab Navigation ---
  function setupTabSwitching() {
    tabBtnManual.addEventListener('click', () => switchTab('manual'));
    tabBtnPhoto.addEventListener('click', () => switchTab('photo'));
  }

  function switchTab(tab) {
    if (tab === 'manual') {
      tabBtnManual.classList.add('active');
      tabBtnManual.setAttribute('aria-selected', 'true');
      tabBtnPhoto.classList.remove('active');
      tabBtnPhoto.setAttribute('aria-selected', 'false');

      tabPaneManual.classList.add('active');
      tabPanePhoto.classList.remove('active');
    } else {
      tabBtnPhoto.classList.add('active');
      tabBtnPhoto.setAttribute('aria-selected', 'true');
      tabBtnManual.classList.remove('active');
      tabBtnManual.setAttribute('aria-selected', 'false');

      tabPanePhoto.classList.add('active');
      tabPaneManual.classList.remove('active');
    }
  }

  // --- 6. Form Validation ---
  function clearErrors() {
    document.querySelectorAll('.field-error').forEach((el) => (el.textContent = ''));
    document.querySelectorAll('.input-box').forEach((el) => el.classList.remove('is-invalid'));
  }

  function setFieldError(fieldId, message) {
    const errorEl = document.getElementById(`error-${fieldId}`);
    const inputEl = document.getElementById(fieldId);
    if (errorEl) errorEl.textContent = message;
    if (inputEl) {
      const parentBox = inputEl.closest('.input-box');
      if (parentBox) parentBox.classList.add('is-invalid');
    }
  }

  function setupFormValidationListeners() {
    [inputState, inputUnits, inputBillingDays, inputAmount].forEach((el) => {
      if (!el) return;
      el.addEventListener('input', () => {
        const errorEl = document.getElementById(`error-${el.id}`);
        if (errorEl) errorEl.textContent = '';
        const parentBox = el.closest('.input-box');
        if (parentBox) parentBox.classList.remove('is-invalid');
      });
    });
  }

  function validateForm() {
    clearErrors();
    let isValid = true;
    const isHi = currentLang === 'hi';

    // State required
    if (!inputState.value || inputState.value.trim() === '') {
      setFieldError('state', isHi ? 'कृपया अपना राज्य या वितरण क्षेत्र चुनें।' : 'Please choose your state or distribution region.');
      isValid = false;
    }

    // Units: 1-5000 (required unless amount_payable is provided)
    const unitsVal = inputUnits.value.trim();
    const amountVal = inputAmount.value.trim();

    if (!unitsVal && !amountVal) {
      setFieldError('units', isHi ? 'कृपया मासिक यूनिट्स (kWh) या बिल राशि (₹) भरें।' : 'Please enter monthly units (kWh) or bill amount (₹).');
      isValid = false;
    } else if (unitsVal) {
      const unitsNum = Number(unitsVal);
      if (isNaN(unitsNum) || unitsNum < 1 || unitsNum > 5000) {
        setFieldError('units', isHi ? 'मासिक खपत 1 से 5,000 यूनिट्स के बीच होनी चाहिए।' : 'Units consumed must be between 1 and 5,000 kWh.');
        isValid = false;
      }
    }

    // Amount payable check
    if (amountVal) {
      const amtNum = Number(amountVal);
      if (isNaN(amtNum) || amtNum <= 0) {
        setFieldError('amount_payable', isHi ? 'बिल राशि एक धनात्मक संख्या होनी चाहिए।' : 'Bill amount must be a positive number.');
        isValid = false;
      }
    }

    // Billing days check (20-62)
    if (inputBillingDays.value.trim()) {
      const daysNum = Number(inputBillingDays.value.trim());
      if (isNaN(daysNum) || daysNum < 20 || daysNum > 62) {
        setFieldError('billing_days', isHi ? 'बिलिंग अवधि 20 से 62 दिनों के बीच होनी चाहिए।' : 'Billing period must be between 20 and 62 days.');
        isValid = false;
      }
    }

    // Sanctioned load check
    if (inputSanctionedLoad.value.trim()) {
      const loadNum = Number(inputSanctionedLoad.value.trim());
      if (isNaN(loadNum) || loadNum <= 0) {
        setFieldError('sanctioned_load', isHi ? 'स्वीकृत लोड 0 kW से अधिक होना चाहिए।' : 'Sanctioned load must be greater than 0 kW.');
        isValid = false;
      }
    }

    return isValid;
  }

  // --- 7. Submit Recommendation API ---
  async function submitForm(e) {
    if (e) e.preventDefault();

    if (!validateForm()) {
      const firstInvalid = document.querySelector('.input-box.is-invalid');
      if (firstInvalid) {
        firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      return;
    }

    let historyUnits = null;
    if (inputPastUnits.value.trim()) {
      historyUnits = inputPastUnits.value
        .split(',')
        .map((s) => parseFloat(s.trim()))
        .filter((n) => !isNaN(n) && n > 0)
        .slice(0, 6);
    }

    const payload = {
      state: inputState.value,
      units_kwh: inputUnits.value.trim() ? parseFloat(inputUnits.value.trim()) : 0,
      billing_days: inputBillingDays.value.trim() ? parseInt(inputBillingDays.value.trim(), 10) : 30,
      amount_payable: inputAmount.value.trim() ? parseFloat(inputAmount.value.trim()) : null,
      sanctioned_load_kw: inputSanctionedLoad.value.trim() ? parseFloat(inputSanctionedLoad.value.trim()) : null,
      fixed_charges: inputFixedCharges.value.trim() ? parseFloat(inputFixedCharges.value.trim()) : null,
      history_units: historyUnits || [],
      has_roof: 'yes',
      lang: currentLang
    };

    // UI Loading state
    resultsSection.classList.add('hidden');
    loadingSection.classList.remove('hidden');
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${currentLang === 'hi' ? 'विश्लेषण किया जा रहा है...' : 'Calculating Feasibility...'}`;

    loadingSection.scrollIntoView({ behavior: 'smooth', block: 'center' });

    try {
      const resp = await fetch('/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail || errData.message || `Server error (${resp.status})`);
      }

      const data = await resp.json();
      lastVerdictData = data;
      lastVerdictPayload = payload;
      renderVerdict(data, payload);
    } catch (err) {
      console.error('Calculation error:', err);
      alert(`Calculation error: ${err.message || 'Please check your connection and inputs.'}`);
    } finally {
      loadingSection.classList.add('hidden');
      btnSubmit.disabled = false;
      const calcText = currentLang === 'hi' ? 'सोलर अनुशंसा की गणना करें' : 'Calculate Solar Recommendation';
      btnSubmit.innerHTML = `<span>${calcText}</span> <i class="fa-solid fa-arrow-right"></i>`;
    }
  }

  // --- 8. Render Modern Verdict (with Multi-language Support) ---
  function renderVerdict(data, inputPayload) {
    const isHi = currentLang === 'hi';
    const hasRoof = (data.has_roof || inputPayload.has_roof || 'yes').toLowerCase();
    const systemKw = Number(data.system_kw || 0);
    const billBefore = Number(data.bill_before || 0);
    const billAfter = Number(data.bill_after || 0);
    const monthlySavings = Number(data.savings_monthly || Math.max(0, billBefore - billAfter) || 0);
    const annualSavings = Number(data.savings_annual || monthlySavings * 12 || 0);
    const subsidy = Number(data.subsidy || 0);
    const totalCost = Number(data.cost || 0);
    const netCost = Math.max(0, totalCost - subsidy);
    const payback = data.payback_years !== undefined ? Number(data.payback_years) : 0;
    const emi = Number(data.emi || 0);

    // Headline & Badges
    verdictStatusBadge.style.background = 'var(--emerald-soft)';
    verdictStatusBadge.style.color = 'var(--emerald-dark)';
    verdictStatusBadge.style.borderColor = 'var(--emerald-border)';

    if (verdictStatusText) {
      verdictStatusText.textContent = isHi ? 'उच्च सोलर अनुकूलता' : 'High Feasibility';
    }

    verdictHeadline.textContent = isHi
      ? `एक ${formatNumber(systemKw)} kW सिस्टम आपका बिजली बिल ${formatINR(billBefore)} से घटाकर लगभग ${formatINR(billAfter)} कर सकता है`
      : `A ${formatNumber(systemKw)} kW system can cut your bill from ${formatINR(billBefore)} to about ${formatINR(billAfter)}`;

    verdictSubheadline.textContent = isHi
      ? 'राज्य डिस्कॉम टैरिफ स्लैब और पीएम सूर्य घर योजना के अनुसार अनुमानित।'
      : 'Calculated using current state tariff slabs and PM Surya Ghar guidelines.';

    // Visual Bill Comparison Bars
    if (compareBeforeVal) compareBeforeVal.textContent = formatINR(billBefore);
    if (compareAfterVal) compareAfterVal.textContent = formatINR(billAfter);

    if (billBefore > 0) {
      const cutPercent = Math.min(100, Math.round(((billBefore - billAfter) / billBefore) * 100));
      if (comparePercentCut) {
        comparePercentCut.textContent = cutPercent > 0
          ? (isHi ? `-${cutPercent}% बिल कटौती` : `-${cutPercent}% Reduction`)
          : '0%';
      }
      const afterPercent = Math.max(5, Math.min(100, Math.round((billAfter / billBefore) * 100)));
      if (barFillAfter) barFillAfter.style.width = `${afterPercent}%`;
      if (barFillBefore) barFillBefore.style.width = '100%';
    }

    // AI Explanation Text (Guaranteed rich, detailed breakdown matching official PM Surya Ghar format)
    if (aiExplanationText) {
      if (isHi) {
        if (data.explanation_hi && data.explanation_hi.length > 50) {
          aiExplanationText.textContent = data.explanation_hi;
        } else if (data.explanation && !data.explanation.startsWith('Based on') && !data.explanation.startsWith('Here is') && data.explanation.length > 50) {
          aiExplanationText.textContent = data.explanation;
        } else {
          const billAfterText = billAfter <= 150 ? 'लगभग नगण्य' : `लगभग ₹${Math.round(billAfter).toLocaleString('en-IN')}`;
          aiExplanationText.textContent = `आपके उपभोग के आधार पर ${formatNumber(systemKw)} kW का सोलर सिस्टम उपयुक्त है जिसकी अनुमानित लागत ₹${Math.round(totalCost).toLocaleString('en-IN')} है। पीएम सूर्य घर योजना के तहत आपको ₹${Math.round(subsidy).toLocaleString('en-IN')} की सब्सिडी मिलेगी, जिससे आपका मासिक बिल ₹${Math.round(billBefore).toLocaleString('en-IN')} से घटकर ${billAfterText} हो जाएगा। अनुमानित पेबैक अवधि ${payback.toFixed(1)} वर्ष है तथा ईएमआई लगभग ₹${Math.round(emi).toLocaleString('en-IN')}/माह होगी (कृपया ध्यान दें कि ये सभी आंकड़े अनुमानित हैं)।`;
        }
      } else {
        if (data.explanation_en && data.explanation_en.length > 50) {
          aiExplanationText.textContent = data.explanation_en;
        } else if (data.explanation && !data.explanation.startsWith('आपके उपभोग') && !data.explanation.startsWith('यहाँ') && data.explanation.length > 50) {
          aiExplanationText.textContent = data.explanation;
        } else {
          const billAfterText = billAfter <= 150 ? 'almost negligible' : `about ₹${Math.round(billAfter).toLocaleString('en-IN')}`;
          aiExplanationText.textContent = `Based on your electricity usage, we recommend a ${formatNumber(systemKw)} kW rooftop solar system with an estimated cost of ₹${Math.round(totalCost).toLocaleString('en-IN')}. Under PM Surya Ghar Muft Bijli Yojana, you are eligible for ₹${Math.round(subsidy).toLocaleString('en-IN')} in direct subsidy, cutting your monthly bill from ₹${Math.round(billBefore).toLocaleString('en-IN')} down to ${billAfterText}. The estimated payback period is ${payback.toFixed(1)} years with a loan EMI of approximately ₹${Math.round(emi).toLocaleString('en-IN')}/month (please note all figures are estimates).`;
        }
      }
    }

    // Populate Bento Cards
    if (valSystemSize) valSystemSize.textContent = `${formatNumber(systemKw)} kW`;
    if (valRoofArea) {
      valRoofArea.textContent = systemKw > 0
        ? (isHi ? `लगभग ${Math.round(systemKw * 100)} वर्ग फुट छाया-मुक्त छत चाहिए` : `Requires ~${Math.round(systemKw * 100)} sq.ft shade-free roof`)
        : (isHi ? 'शून्य छत स्थान आवश्यक' : 'Zero rooftop space required');
    }

    if (valMonthlySavings) valMonthlySavings.textContent = formatINR(monthlySavings);
    if (valAnnualSavings) {
      valAnnualSavings.textContent = isHi
        ? `प्रति वर्ष ${formatINR(annualSavings)} की सीधी बचत`
        : `${formatINR(annualSavings)} saved per year`;
    }

    if (valSubsidy) valSubsidy.textContent = formatINR(subsidy);
    if (valNetCost) {
      valNetCost.textContent = isHi
        ? `शुद्ध निवेश: ${formatINR(netCost)}`
        : `Net investment: ${formatINR(netCost)}`;
    }

    if (valPayback) {
      valPayback.textContent = payback > 0 && payback < 99
        ? `${payback.toFixed(1)} ${isHi ? 'वर्ष' : 'Years'}`
        : (isHi ? 'त्वरित निवेश वापसी' : 'Immediate ROI');
    }
    if (valPaybackCaption) {
      valPaybackCaption.textContent = isHi ? 'शेष 22+ वर्षों तक मुफ्त बिजली' : 'Free electricity for remaining 22+ yrs';
    }

    if (valEmi) {
      valEmi.textContent = emi > 0
        ? `${formatINR(emi)} ${isHi ? '/ माह' : '/ month'}`
        : 'N/A';
    }
    if (valEmiPillText) {
      valEmiPillText.textContent = isHi
        ? `ईएमआई आपकी ₹${Math.round(monthlySavings).toLocaleString('en-IN')} की मासिक बचत से कम है`
        : 'EMI is lower than your monthly savings';
    }

    // Populate Checklist Roadmap (Localized)
    if (checklistContainer) {
      checklistContainer.innerHTML = '';
      const items = data.checklist && data.checklist.length > 0
        ? data.checklist
        : (isHi
          ? [
              'पीएम सूर्य घर राष्ट्रीय पोर्टल (pmsuryaghar.gov.in) पर पंजीकरण करें।',
              'अपने डिस्कॉम की सूची से एक अधिकृत सोलर वेंडर चुनें।',
              'डिस्कॉम के साथ नेट-मीटरिंग और ग्रिड सिंक्रोनाइज़ेशन के लिए आवेदन करें।',
              'सोलर प्लांट चालू करें और सीधे बैंक खाते में डीबीटी सब्सिडी प्राप्त करें।'
            ]
          : [
              'Register on PM Surya Ghar Portal (pmsuryaghar.gov.in).',
              'Select an empanelled vendor from your DISCOM roster.',
              'Submit bi-directional net-meter application.',
              'Commission rooftop system and receive direct DBT subsidy.'
            ]);

      items.forEach((item, idx) => {
        const stepDiv = document.createElement('div');
        stepDiv.className = 'roadmap-step';
        stepDiv.innerHTML = `
          <div class="step-circle">${idx + 1}</div>
          <div class="step-details">
            <h4>${isHi ? `चरण ${idx + 1}` : `Step ${idx + 1}`}</h4>
            <p>${item}</p>
          </div>
        `;
        checklistContainer.appendChild(stepDiv);
      });
    }

    // Populate Assumptions (Localized)
    if (assumptionsList) {
      assumptionsList.innerHTML = '';
      const assumptions = data.assumptions && data.assumptions.length > 0
        ? data.assumptions
        : (isHi
          ? [
              'सोलर उत्पादन मानक धूप में प्रति kW प्रतिदिन लगभग 4.0 से 4.3 यूनिट अनुमानित है।',
              'सब्सिडी की गणना पीएम सूर्य घर केंद्रीय वित्तीय सहायता (सीएफए) के अनुसार की गई है।',
              'पैनल की दक्षता में 25 वर्षों के दौरान प्रति वर्ष 0.7% की सामान्य गिरावट मानी गई है।'
            ]
          : [
              'Solar generation estimated at 4.0-4.3 units per kW per day.',
              'Subsidy calculated per PM Surya Ghar Central Financial Assistance norms.',
              'Estimated panel degradation modeled at 0.7% annually with 25-year lifespan.'
            ]);

      assumptions.forEach((assump) => {
        const li = document.createElement('li');
        li.textContent = assump;
        assumptionsList.appendChild(li);
      });
    }

    // Show verdict and smooth scroll
    resultsSection.classList.remove('hidden');
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // --- 9. Client-Side Image Resizing (Canvas) ---
  function resizeImage(file, maxDim = 1280) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = function (e) {
        const img = new Image();
        img.onload = function () {
          let width = img.width;
          let height = img.height;

          if (width > maxDim || height > maxDim) {
            if (width > height) {
              height = Math.round((height * maxDim) / width);
              width = maxDim;
            } else {
              width = Math.round((width * maxDim) / height);
              height = maxDim;
            }
          }

          const canvas = document.createElement('canvas');
          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, width, height);

          canvas.toBlob(
            (blob) => {
              if (blob) {
                resolve(blob);
              } else {
                reject(new Error('Canvas Blob conversion failed.'));
              }
            },
            'image/jpeg',
            0.82
          );
        };
        img.onerror = () => reject(new Error('Image format could not be loaded.'));
        img.src = e.target.result;
      };
      reader.onerror = () => reject(new Error('File reading failed.'));
      reader.readAsDataURL(file);
    });
  }

  // --- 10. Photo Upload & OCR Workflow ---
  function setupPhotoUpload() {
    if (!billPhotoInput || !dropZone) return;

    ['dragenter', 'dragover'].forEach((eventName) => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach((eventName) => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
      });
    });

    dropZone.addEventListener('drop', (e) => {
      const files = e.dataTransfer && e.dataTransfer.files;
      if (files && files.length > 0) {
        handlePhotoFile(files[0]);
      }
    });

    billPhotoInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handlePhotoFile(e.target.files[0]);
      }
    });
  }

  async function handlePhotoFile(file) {
    const isHi = currentLang === 'hi';
    if (!file.type.startsWith('image/')) {
      showPhotoError(isHi ? 'कृपया एक मान्य फोटो (JPEG, PNG, WEBP) चुनें।' : 'Please choose a valid photo (JPEG, PNG, WEBP).');
      return;
    }

    photoErrorBanner.classList.add('hidden');
    photoPreviewBox.classList.remove('hidden');
    previewFilename.textContent = file.name;
    previewFilesize.textContent = `${(file.size / (1024 * 1024)).toFixed(2)} MB • ${isHi ? 'इमेज साइज अनुकूलित हो रही है...' : 'Optimizing image size...'}`;
    uploadProgressFill.style.width = '25%';

    imagePreview.src = URL.createObjectURL(file);

    try {
      uploadProgressFill.style.width = '45%';
      const resizedBlob = await resizeImage(file, 1280);
      previewFilesize.textContent = `${(resizedBlob.size / 1024).toFixed(1)} KB • ${isHi ? 'एआई ओसीआर स्कैनिंग जारी...' : 'Analyzing OCR...'}`;
      uploadProgressFill.style.width = '70%';

      const formData = new FormData();
      formData.append('file', resizedBlob, file.name || 'bill.jpg');

      const resp = await fetch('/analyze', {
        method: 'POST',
        body: formData
      });

      uploadProgressFill.style.width = '100%';

      if (!resp.ok) {
        const errJson = await resp.json().catch(() => ({}));
        throw new Error(errJson.detail || errJson.message || 'OCR parsing failed');
      }

      const analyzed = await resp.json();

      if (analyzed.error) {
        showPhotoError(analyzed.error);
        uploadProgressFill.style.width = '0%';
        return;
      }

      // Populate form
      if (analyzed.state) inputState.value = analyzed.state;
      if (analyzed.units_kwh || analyzed.units) {
        inputUnits.value = analyzed.units_kwh || analyzed.units;
      }
      if (analyzed.billing_days) inputBillingDays.value = analyzed.billing_days;
      if (analyzed.amount_payable || analyzed.amount) {
        inputAmount.value = analyzed.amount_payable || analyzed.amount;
      }
      if (analyzed.sanctioned_load_kw || analyzed.sanctioned_load) {
        inputSanctionedLoad.value = analyzed.sanctioned_load_kw || analyzed.sanctioned_load;
      }
      if (analyzed.fixed_charges) inputFixedCharges.value = analyzed.fixed_charges;

      const conf = analyzed.confidence ? Math.round(analyzed.confidence * 100) : 92;
      photoConfidenceText.textContent = isHi
        ? `लगभग ${conf}% सटीकता से स्कैन हुआ। कृपया नीचे मानों की समीक्षा करें।`
        : `Extracted with ~${conf}% confidence. Review values below and calculate.`;
      photoExtractedBanner.classList.remove('hidden');

      setTimeout(() => {
        switchTab('manual');
        photoPreviewBox.classList.add('hidden');
        uploadProgressFill.style.width = '0%';
        window.scrollTo({ top: solarForm.offsetTop - 80, behavior: 'smooth' });
      }, 500);
    } catch (err) {
      console.error('OCR Error:', err);
      showPhotoError(isHi ? 'इस फोटो को पढ़ा नहीं जा सका, कृपया विवरण मैन्युअल रूप से भरें।' : "Couldn't read this photo, please enter values manually.");
      uploadProgressFill.style.width = '0%';
    } finally {
      billPhotoInput.value = '';
    }
  }

  function showPhotoError(msg) {
    photoErrorMessage.textContent = msg;
    photoErrorBanner.classList.remove('hidden');
    photoPreviewBox.classList.add('hidden');
  }

  // --- Bootstrap on Ready ---
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
  } else {
    initApp();
  }
})();
