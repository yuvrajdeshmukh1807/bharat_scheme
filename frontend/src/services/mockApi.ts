// frontend/src/services/mockApi.ts
import { SCHEMES_DATA, CATEGORIES_METADATA } from '../data/schemesData';

// Helper for trilingual string extraction
function getLocalized(obj: any, key: string, lang: string, fallbackKey: string = `${key}_en`): any {
  return obj[`${key}_${lang}`] || obj[fallbackKey] || obj[key] || '';
}

// 1. Categories with counts
export function mockGetCategories(lang: string = 'en') {
  const counts: Record<string, number> = {};
  for (const s of SCHEMES_DATA) {
    counts[s.category] = (counts[s.category] || 0) + 1;
  }
  return CATEGORIES_METADATA.map((cat: any) => ({
    ...cat,
    scheme_count: counts[cat.id] || 0
  }));
}

// 2. Featured schemes
export function mockGetFeatured(lang: string = 'en') {
  const featuredIds = [
    'pm-kisan',
    'ayushman-bharat-pmjay',
    'pm-mudra-yojana',
    'sukanya-samriddhi-yojana',
    'majhi-ladki-bahin-maharashtra',
    'central-sector-scholarship-pm-usp'
  ];
  return SCHEMES_DATA
    .filter(s => featuredIds.includes(s.id))
    .map(s => ({
      id: s.id,
      slug: s.slug,
      title: getLocalized(s, 'title', lang),
      category: s.category,
      level: s.level,
      state_name: s.state_name,
      ministry: s.ministry,
      brief: getLocalized(s, 'brief', lang),
      benefits: s[`benefits_${lang}` as keyof typeof s] || s.benefits_en,
      official_portal_url: s.official_portal_url,
      application_mode: s.application_mode
    }));
}

// 3. Scheme listing with search & filters
export function mockGetSchemes(params: URLSearchParams) {
  const category = params.get('category');
  const level = params.get('level');
  const state = params.get('state');
  const search = params.get('search');
  const lang = params.get('language') || 'en';

  let filtered = [...SCHEMES_DATA];

  if (category && category !== 'All') {
    filtered = filtered.filter(s => s.category.toLowerCase() === category.toLowerCase());
  }

  if (level && level !== 'All') {
    filtered = filtered.filter(s => s.level.toLowerCase() === level.toLowerCase());
  }

  if (state && state !== 'All') {
    filtered = filtered.filter(s => 
      s.state_name.toLowerCase() === state.toLowerCase() || 
      s.state_name.toLowerCase() === 'all india'
    );
  }

  if (search) {
    const q = search.toLowerCase().trim();
    filtered = filtered.filter(s =>
      s.title_en.toLowerCase().includes(q) ||
      (s.title_hi && s.title_hi.toLowerCase().includes(q)) ||
      (s.title_mr && s.title_mr.toLowerCase().includes(q)) ||
      s.brief_en.toLowerCase().includes(q) ||
      (s.tags && s.tags.some((t: string) => t.toLowerCase().includes(q)))
    );
  }

  return filtered.map(s => ({
    id: s.id,
    slug: s.slug,
    title: getLocalized(s, 'title', lang),
    title_en: s.title_en,
    title_hi: s.title_hi,
    title_mr: s.title_mr,
    category: s.category,
    level: s.level,
    state_name: s.state_name,
    ministry: s.ministry,
    brief: getLocalized(s, 'brief', lang),
    benefits: s[`benefits_${lang}` as keyof typeof s] || s.benefits_en,
    official_portal_url: s.official_portal_url,
    application_mode: s.application_mode,
    helpline_number: s.helpline_number,
    tags: s.tags || []
  }));
}

// 4. Scheme detail
export function mockGetSchemeDetail(idOrSlug: string, lang: string = 'en') {
  const scheme = SCHEMES_DATA.find(s => s.id === idOrSlug || s.slug === idOrSlug);
  if (!scheme) return null;

  return {
    id: scheme.id,
    slug: scheme.slug,
    title: getLocalized(scheme, 'title', lang),
    title_en: scheme.title_en,
    title_hi: scheme.title_hi,
    title_mr: scheme.title_mr,
    ministry: scheme.ministry,
    level: scheme.level,
    state_name: scheme.state_name,
    category: scheme.category,
    brief: getLocalized(scheme, 'brief', lang),
    description: getLocalized(scheme, 'description', lang),
    benefits: scheme[`benefits_${lang}` as keyof typeof scheme] || scheme.benefits_en,
    eligibility_summary: getLocalized(scheme, 'eligibility_summary', lang),
    eligibility_criteria: scheme.eligibility_criteria,
    documents_required: scheme[`documents_required_${lang}` as keyof typeof scheme] || scheme.documents_required_en,
    application_steps: scheme[`application_steps_${lang}` as keyof typeof scheme] || scheme.application_steps_en,
    official_portal_url: scheme.official_portal_url,
    application_mode: scheme.application_mode,
    helpline_number: scheme.helpline_number,
    tags: scheme.tags || []
  };
}

// 5. Eligibility matching engine (pure TypeScript port of Python rule engine)
export function mockCheckEligibility(profile: any) {
  const lang = profile.language || 'en';
  const results = SCHEMES_DATA.map(scheme => {
    const rules = (scheme.eligibility_criteria || {}) as Record<string, any>;
    const matched_reasons: string[] = [];
    const unmet_reasons: string[] = [];
    const info_needed: string[] = [];
    const criteria_evaluations: any[] = [];
    let score = 100;
    let hard_disqualification = false;

    // 1. State / Jurisdiction
    const appStates: string[] = rules.applicable_states || ['All India'];
    if (appStates.includes('All India')) {
      matched_reasons.push(
        lang === 'hi' ? 'पूरे देश में सभी राज्यों में लागू' :
        lang === 'mr' ? 'संपूर्ण देशभरात सर्व राज्यांसाठी लागू' :
        'Applicable nationwide across all States and Union Territories'
      );
      criteria_evaluations.push({ criteria_name: 'Jurisdiction', status: 'matched', message: `All India (${profile.state})` });
    } else if (appStates.map(s => s.toLowerCase()).includes((profile.state || '').toLowerCase())) {
      matched_reasons.push(
        lang === 'hi' ? `आपके राज्य के अनुकूल: ${profile.state}` :
        lang === 'mr' ? `तुमच्या राज्यासाठी लागू: ${profile.state}` :
        `Matches your state: ${profile.state}`
      );
      criteria_evaluations.push({ criteria_name: 'Jurisdiction', status: 'matched', message: `State (${profile.state})` });
    } else {
      hard_disqualification = true;
      score -= 60;
      unmet_reasons.push(
        lang === 'hi' ? `यह योजना केवल ${appStates.join(', ')} के लिए है।` :
        lang === 'mr' ? `ही योजना केवळ ${appStates.join(', ')} साठी आहे.` :
        `Scheme is strictly restricted to ${appStates.join(', ')}. Selected: ${profile.state}.`
      );
      criteria_evaluations.push({ criteria_name: 'Jurisdiction', status: 'unmet', message: `Restricted to ${appStates.join(', ')}` });
    }

    // 2. Gender
    const reqGender = (rules.gender || 'all').toLowerCase();
    if (reqGender !== 'all') {
      if ((profile.gender || '').toLowerCase() === reqGender) {
        matched_reasons.push(
          lang === 'hi' ? `लिंग पात्रता पूर्ण: ${reqGender} के लिए विशेष` :
          lang === 'mr' ? `लिंग निकष पूर्ण: ${reqGender} साठी राखीव` :
          `Matches gender criteria: exclusively for ${reqGender}`
        );
        criteria_evaluations.push({ criteria_name: 'Gender', status: 'matched', message: `Matches (${reqGender})` });
      } else {
        hard_disqualification = true;
        score -= 50;
        unmet_reasons.push(
          lang === 'hi' ? `यह योजना केवल ${reqGender} आवेदकों के लिए है।` :
          lang === 'mr' ? `ही योजना केवळ ${reqGender} अर्जदारांसाठी आहे.` :
          `Scheme is exclusively for ${reqGender} applicants.`
        );
        criteria_evaluations.push({ criteria_name: 'Gender', status: 'unmet', message: `Requires ${reqGender}` });
      }
    } else {
      criteria_evaluations.push({ criteria_name: 'Gender', status: 'matched', message: 'Open to all genders' });
    }

    // 3. Age
    const minAge = rules.min_age !== undefined ? rules.min_age : 0;
    const maxAge = rules.max_age !== undefined ? rules.max_age : 120;
    const age = Number(profile.age) || 0;
    if (age >= minAge && age <= maxAge) {
      matched_reasons.push(
        lang === 'hi' ? `आयु ${age} वर्ष पात्र श्रेणी (${minAge}-${maxAge} वर्ष) में है` :
        lang === 'mr' ? `वय ${age} वर्षे पात्र वयोगटात (${minAge}-${maxAge} वर्षे) बसते` :
        `Age ${age} is within eligible bracket (${minAge} to ${maxAge} years)`
      );
      criteria_evaluations.push({ criteria_name: 'Age', status: 'matched', message: `${age} yrs (${minAge}-${maxAge})` });
    } else {
      hard_disqualification = true;
      score -= 40;
      unmet_reasons.push(
        lang === 'hi' ? `आयु ${age} वर्ष आवश्यक सीमा (${minAge}-${maxAge} वर्ष) से बाहर है` :
        lang === 'mr' ? `वय ${age} वर्षे आवश्यक मर्यादेबाहेर (${minAge}-${maxAge} वर्षे) आहे` :
        `Age ${age} is outside eligible bracket (${minAge} to ${maxAge} years)`
      );
      criteria_evaluations.push({ criteria_name: 'Age', status: 'unmet', message: `Requires ${minAge}-${maxAge} yrs` });
    }

    // 4. Caste category
    const allowedCastes: string[] = rules.caste_categories || ['All'];
    if (allowedCastes.includes('All') || allowedCastes.map(c => c.toLowerCase()).includes((profile.caste_category || '').toLowerCase())) {
      matched_reasons.push(
        lang === 'hi' ? `जाति/सामाजिक श्रेणी अनुकूल: ${profile.caste_category}` :
        lang === 'mr' ? `सामाजिक प्रवर्ग लागू: ${profile.caste_category}` :
        `Category eligible: ${profile.caste_category}`
      );
      criteria_evaluations.push({ criteria_name: 'Caste', status: 'matched', message: `${profile.caste_category}` });
    } else {
      score -= 30;
      unmet_reasons.push(`Reserved for ${allowedCastes.join(', ')}.`);
      criteria_evaluations.push({ criteria_name: 'Caste', status: 'unmet', message: `Requires ${allowedCastes.join(', ')}` });
    }

    // 5. Income limit
    const incomeLimit = rules.max_annual_income;
    const userIncome = Number(profile.annual_income) || 0;
    if (incomeLimit !== undefined && incomeLimit !== null) {
      if (userIncome <= incomeLimit) {
        matched_reasons.push(
          lang === 'hi' ? `पारिवारिक आय ₹${userIncome.toLocaleString('en-IN')} सीमा (₹${incomeLimit.toLocaleString('en-IN')}) के भीतर है` :
          lang === 'mr' ? `कौटुंबिक उत्पन्न ₹${userIncome.toLocaleString('en-IN')} मर्यादेत (₹${incomeLimit.toLocaleString('en-IN')}) आहे` :
          `Income ₹${userIncome.toLocaleString('en-IN')} is within ceiling (₹${incomeLimit.toLocaleString('en-IN')})`
        );
        criteria_evaluations.push({ criteria_name: 'Income', status: 'matched', message: `Under ₹${incomeLimit.toLocaleString('en-IN')}` });
      } else {
        hard_disqualification = true;
        score -= 50;
        unmet_reasons.push(
          lang === 'hi' ? `पारिवारिक आय सीमा ₹${incomeLimit.toLocaleString('en-IN')} से अधिक है` :
          lang === 'mr' ? `कौटुंबिक उत्पन्न मर्यादा ₹${incomeLimit.toLocaleString('en-IN')} पेक्षा जास्त आहे` :
          `Annual income exceeds scheme limit of ₹${incomeLimit.toLocaleString('en-IN')}`
        );
        criteria_evaluations.push({ criteria_name: 'Income', status: 'unmet', message: `Exceeds ₹${incomeLimit.toLocaleString('en-IN')}` });
      }
    }

    // 6. Farmer check
    if (rules.is_farmer_required) {
      if (profile.is_farmer) {
        matched_reasons.push('Registered farmer profile confirmed');
        criteria_evaluations.push({ criteria_name: 'Occupation', status: 'matched', message: 'Farmer' });
      } else {
        hard_disqualification = true;
        score -= 50;
        unmet_reasons.push('Requires beneficiary to be an active farmer');
        criteria_evaluations.push({ criteria_name: 'Occupation', status: 'unmet', message: 'Requires Farmer' });
      }
    }

    // 7. Student check
    if (rules.is_student_required) {
      if (profile.student_status) {
        matched_reasons.push('Enrolled student status verified');
        criteria_evaluations.push({ criteria_name: 'Student Status', status: 'matched', message: 'Enrolled student' });
      } else {
        hard_disqualification = true;
        score -= 50;
        unmet_reasons.push('Exclusively for currently enrolled students');
        criteria_evaluations.push({ criteria_name: 'Student Status', status: 'unmet', message: 'Requires Student' });
      }
    }

    // 8. Disability check
    if (rules.requires_differently_abled) {
      if (profile.is_differently_abled) {
        matched_reasons.push('Differently-abled / Divyangjan qualification matched');
        criteria_evaluations.push({ criteria_name: 'Disability', status: 'matched', message: 'Divyangjan' });
      } else {
        hard_disqualification = true;
        score -= 50;
        unmet_reasons.push('Scheme requires applicant to have recognized disability certificate');
        criteria_evaluations.push({ criteria_name: 'Disability', status: 'unmet', message: 'Requires Divyangjan' });
      }
    }

    // Final Status & Clamping
    score = Math.max(10, Math.min(100, score));
    let match_status: 'ELIGIBLE' | 'POTENTIALLY_ELIGIBLE' | 'NOT_ELIGIBLE';
    if (hard_disqualification || unmet_reasons.length > 0) {
      match_status = 'NOT_ELIGIBLE';
    } else if (score >= 80) {
      match_status = 'ELIGIBLE';
    } else {
      match_status = 'POTENTIALLY_ELIGIBLE';
    }

    return {
      scheme_id: scheme.id,
      slug: scheme.slug,
      title: getLocalized(scheme, 'title', lang),
      category: scheme.category,
      level: scheme.level,
      state_name: scheme.state_name,
      ministry: scheme.ministry,
      brief: getLocalized(scheme, 'brief', lang),
      benefits: scheme[`benefits_${lang}` as keyof typeof scheme] || scheme.benefits_en,
      match_status,
      match_score: score,
      matched_reasons,
      unmet_reasons,
      info_needed,
      criteria_evaluations,
      official_portal_url: scheme.official_portal_url,
      application_mode: scheme.application_mode,
      helpline_number: scheme.helpline_number
    };
  });

  // Sort: ELIGIBLE first (desc score), then POTENTIALLY_ELIGIBLE, then NOT_ELIGIBLE
  const order: Record<string, number> = { ELIGIBLE: 0, POTENTIALLY_ELIGIBLE: 1, NOT_ELIGIBLE: 2 };
  results.sort((a, b) => (order[a.match_status] - order[b.match_status]) || (b.match_score - a.match_score));

  return {
    total_schemes_analyzed: SCHEMES_DATA.length,
    eligible_count: results.filter(r => r.match_status === 'ELIGIBLE').length,
    potentially_eligible_count: results.filter(r => r.match_status === 'POTENTIALLY_ELIGIBLE').length,
    not_eligible_count: results.filter(r => r.match_status === 'NOT_ELIGIBLE').length,
    user_summary: profile,
    results
  };
}

// 6. Conversational RAG assistant query simulator (Offline Grounded)
export function mockAssistantChat(query: string, lang: string = 'en') {
  const q = query.toLowerCase().trim();
  
  // Keyword relevance scoring
  const scored = SCHEMES_DATA.map(s => {
    let score = 0;
    const text = `${s.title_en} ${s.title_hi || ''} ${s.title_mr || ''} ${s.brief_en} ${s.category} ${(s.tags || []).join(' ')}`.toLowerCase();
    for (const word of q.split(/\s+/)) {
      if (word.length > 2 && text.includes(word)) score += 1;
    }
    return { scheme: s, score };
  }).filter(item => item.score > 0);

  scored.sort((a, b) => b.score - a.score);
  const matched: any[] = (scored.length > 0 ? scored.slice(0, 3) : [{ scheme: SCHEMES_DATA[0], score: 1 }]).map(x => x.scheme);
  const primary: any = matched[0] || (SCHEMES_DATA[0] as any);

  const citations = matched.map(s => ({
    scheme_id: s.id,
    title: getLocalized(s, 'title', lang),
    official_portal_url: s.official_portal_url,
    relevance_score: 0.95
  }));

  const followups = lang === 'hi' ? [
    `${primary.title_hi || primary.title_en} के लिए कौन से दस्तावेज चाहिए?`,
    'ऑनलाइन आवेदन करने की प्रक्रिया क्या है?',
    'क्या इसके लिए आय प्रमाण पत्र जरूरी है?'
  ] : lang === 'mr' ? [
    `${primary.title_mr || primary.title_en} साठी कोणती कागदपत्रे लागतात?`,
    'ऑनलाईन अर्ज कसा करावा?',
    'उत्पन्नाचा दाखला आवश्यक आहे का?'
  ] : [
    `What are the required documents for ${primary.title_en}?`,
    `How do I apply online for ${primary.title_en}?`,
    `What is the official helpline number for ${primary.title_en}?`
  ];

  let answerText = '';
  if (lang === 'hi') {
    answerText = `**${primary.title_hi || primary.title_en}** (${primary.ministry}):\n\n` +
      `• **विवरण:** ${primary.brief_hi || primary.brief_en}\n` +
      `• **प्रमुख लाभ:** ${(primary.benefits_hi || primary.benefits_en).slice(0, 2).join('; ')}\n` +
      `• **पात्रता:** ${primary.eligibility_summary_hi || primary.eligibility_summary_en}\n` +
      `• **आधिकारिक पोर्टल:** [${primary.official_portal_url}](${primary.official_portal_url})\n` +
      `• **हेल्पलाइन:** ${primary.helpline_number || 'उपलब्ध नहीं'}`;
  } else if (lang === 'mr') {
    answerText = `**${primary.title_mr || primary.title_en}** (${primary.ministry}):\n\n` +
      `• **माहिती:** ${primary.brief_mr || primary.brief_en}\n` +
      `• **फायदे:** ${(primary.benefits_mr || primary.benefits_en).slice(0, 2).join('; ')}\n` +
      `• **पात्रता:** ${primary.eligibility_summary_mr || primary.eligibility_summary_en}\n` +
      `• **अधिकृत संकेतस्थळ:** [${primary.official_portal_url}](${primary.official_portal_url})\n` +
      `• **हेल्पलाईन:** ${primary.helpline_number || 'उपलब्ध नाही'}`;
  } else {
    answerText = `**${primary.title_en}** (${primary.ministry}):\n\n` +
      `• **Overview:** ${primary.brief_en}\n` +
      `• **Key Benefits:** ${primary.benefits_en.slice(0, 2).join('; ')}\n` +
      `• **Eligibility Summary:** ${primary.eligibility_summary_en}\n` +
      `• **Official Portal:** [${primary.official_portal_url}](${primary.official_portal_url})\n` +
      `• **Helpline:** ${primary.helpline_number || 'N/A'}`;
  }

  return {
    query,
    language: lang,
    answer: answerText,
    citations,
    suggested_followups: followups,
    referenced_schemes: matched.map(s => ({
      id: s.id,
      title: getLocalized(s, 'title', lang),
      category: s.category,
      brief: getLocalized(s, 'brief', lang),
      portal: s.official_portal_url,
      helpline: s.helpline_number
    }))
  };
}

// 7. Transparent Window Fetch Interceptor
export function installMockFetch() {
  if (typeof window === 'undefined') return;

  const originalFetch = window.fetch.bind(window);

  window.fetch = async function (input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    const urlStr = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;

    // Check if this is an API call
    if (urlStr.includes('/api/')) {
      const url = new URL(urlStr, window.location.origin);
      const pathname = url.pathname;
      const searchParams = url.searchParams;
      const lang = searchParams.get('language') || 'en';

      try {
        // Health check
        if (pathname === '/api/health') {
          return new Response(JSON.stringify({
            status: 'healthy',
            service: 'BharatScheme AI (Standalone Mode)',
            version: '1.0.0',
            schemes_indexed: SCHEMES_DATA.length
          }), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }

        // Categories
        if (pathname === '/api/categories') {
          const data = mockGetCategories(lang);
          return new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }

        // Featured schemes
        if (pathname === '/api/featured') {
          const data = mockGetFeatured(lang);
          return new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }

        // Scheme list
        if (pathname === '/api/schemes') {
          const data = mockGetSchemes(searchParams);
          return new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }

        // Single scheme detail: /api/schemes/:id
        const detailMatch = pathname.match(/^\/api\/schemes\/([^/]+)$/);
        if (detailMatch) {
          const idOrSlug = detailMatch[1];
          const data = mockGetSchemeDetail(idOrSlug, lang);
          if (data) {
            return new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } });
          } else {
            return new Response(JSON.stringify({ detail: 'Scheme not found' }), { status: 404, headers: { 'Content-Type': 'application/json' } });
          }
        }

        // Eligibility check
        if (pathname === '/api/eligibility/check' && init?.method === 'POST') {
          const body = typeof init.body === 'string' ? JSON.parse(init.body) : {};
          const data = mockCheckEligibility(body);
          return new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }

        // Assistant chat
        if (pathname === '/api/assistant/chat' && init?.method === 'POST') {
          const body = typeof init.body === 'string' ? JSON.parse(init.body) : {};
          const data = mockAssistantChat(body.query || '', body.language || 'en');
          return new Response(JSON.stringify(data), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }

        // Saved schemes: fall back to empty list or local mock
        if (pathname === '/api/saved-schemes') {
          return new Response(JSON.stringify([]), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }
      } catch (err) {
        console.error('[Mock API Interceptor Error]:', err);
      }
    }

    // Default to real fetch if not intercepted
    return originalFetch(input, init);
  };

  console.log('[BharatScheme AI] Standalone client-side API layer activated. No external backend required.');
}
