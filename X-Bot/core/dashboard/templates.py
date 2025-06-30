"""
Templates HTML du Dashboard
"""

from .config import DashboardConfig, DARK_THEME


def get_dashboard_html(config: DashboardConfig) -> str:
    """Génère l'interface HTML complète du dashboard"""
    
    theme = DARK_THEME
    refresh_interval = config.auto_refresh_interval * 1000
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{config.title}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: {theme["primary_bg"]};
                color: {theme["primary_color"]};
                line-height: 1.6;
            }}
            
            .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
            
            .header {{ 
                text-align: center; 
                margin-bottom: 30px;
                padding: 20px;
                background: {theme["secondary_bg"]};
                border-radius: 10px;
            }}
            
            .tabs {{ 
                display: flex; 
                margin-bottom: 20px; 
                background: {theme["secondary_bg"]};
                border-radius: 10px;
                overflow: hidden;
            }}
            
            .tab {{ 
                flex: 1; 
                padding: 15px; 
                background: {theme["accent_bg"]}; 
                border: none; 
                color: {theme["secondary_color"]}; 
                cursor: pointer; 
                transition: all 0.3s;
            }}
            
            .tab:hover {{ background: #475569; color: {theme["primary_color"]}; }}
            .tab.active {{ background: {theme["accent_color"]}; color: white; }}
            
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
            
            .metrics-grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                gap: 20px; 
                margin-bottom: 30px; 
            }}
            
            .metric-card {{ 
                background: {theme["secondary_bg"]}; 
                padding: 20px; 
                border-radius: 10px; 
                border-left: 4px solid {theme["accent_color"]};
            }}
            
            .metric-value {{ 
                font-size: 2rem; 
                font-weight: bold; 
                color: {theme["accent_color"]}; 
            }}
            
            .metric-label {{ 
                color: {theme["secondary_color"]}; 
                margin-top: 5px; 
            }}
            
            .btn {{ 
                background: {theme["accent_color"]}; 
                color: white; 
                border: none; 
                padding: 12px 24px; 
                border-radius: 8px; 
                cursor: pointer; 
                font-size: 14px;
                font-weight: 500;
                transition: all 0.3s;
                margin-right: 10px;
            }}
            
            .btn:hover {{ background: #2563eb; transform: translateY(-1px); }}
            
            /* Configuration Styles */
            .config-sections {{ padding: 20px; }}
            .section-header {{ 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                margin-bottom: 30px;
                padding-bottom: 15px;
                border-bottom: 2px solid {theme["accent_bg"]};
            }}
            
            .config-grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); 
                gap: 20px; 
            }}
            
            .config-section {{ 
                background: {theme["secondary_bg"]}; 
                padding: 20px; 
                border-radius: 10px; 
                border-left: 4px solid {theme["accent_color"]};
            }}
            
            .config-section h3 {{ 
                margin-bottom: 15px; 
                color: {theme["accent_color"]}; 
            }}
            
            .form-group {{ 
                margin-bottom: 15px; 
            }}
            
            .form-group label {{ 
                display: block; 
                margin-bottom: 5px; 
                color: {theme["secondary_color"]}; 
                font-weight: 500;
            }}
            
            .form-group input, .form-group select, .form-group textarea {{ 
                width: 100%; 
                padding: 8px 12px; 
                border: 1px solid {theme["accent_bg"]}; 
                border-radius: 6px; 
                background: {theme["primary_bg"]}; 
                color: {theme["primary_color"]}; 
                font-size: 14px;
            }}
            
            .form-group input[type="checkbox"] {{ 
                width: auto; 
                margin-right: 8px; 
            }}
            
            .form-group input[type="range"] {{ 
                margin-right: 10px; 
            }}
            
            /* Prompts Styles */
            .prompts-grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); 
                gap: 20px; 
            }}
            
            .prompt-section {{ 
                background: {theme["secondary_bg"]}; 
                padding: 20px; 
                border-radius: 10px; 
                border-left: 4px solid #10b981;
            }}
            
            .prompt-section h3 {{ 
                margin-bottom: 15px; 
                color: #10b981; 
            }}
            
            textarea {{ 
                resize: vertical; 
                min-height: 80px; 
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            }}
            
            .status-indicator {{ 
                display: inline-block; 
                width: 8px; 
                height: 8px; 
                border-radius: 50%; 
                margin-right: 8px; 
            }}
            
            .status-online {{ background: #10b981; }}
            .status-offline {{ background: #ef4444; }}
            .status-warning {{ background: #f59e0b; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 {config.title}</h1>
                <p>{config.description}</p>
                <button class="btn" onclick="refreshData()">🔄 Actualiser</button>
            </div>
            
            <div class="tabs">
                <button class="tab active" onclick="showTab('overview')">📊 Vue d'ensemble</button>
                <button class="tab" onclick="showTab('performance')">📈 Performance</button>
                <button class="tab" onclick="showTab('config')">⚙️ Configuration</button>
                <button class="tab" onclick="showTab('prompts')">💬 Prompts</button>
                <button class="tab" onclick="showTab('test')">🧪 Test Types</button>
            </div>
            
            <div id="overview" class="tab-content active">
                <div class="metrics-grid" id="metrics">
                    <div class="metric-card">
                        <div class="metric-value" id="status">Chargement...</div>
                        <div class="metric-label">Statut</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="uptime">--</div>
                        <div class="metric-label">Uptime</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="tweets">--</div>
                        <div class="metric-label">Tweets aujourd'hui</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value" id="likes">--</div>
                        <div class="metric-label">Likes aujourd'hui</div>
                    </div>
                </div>
            </div>
            
            <div id="performance" class="tab-content">
                <div class="config-sections">
                    <div class="section-header">
                        <h2>📈 Performance des Tweets</h2>
                        <div>
                            <button class="btn" onclick="collectStatsNow()">🔄 Collecter Stats</button>
                            <button class="btn" onclick="refreshPerformance()">📊 Actualiser</button>
                        </div>
                    </div>
                    
                    <!-- Performance Overview -->
                    <div class="metrics-grid" id="performance-overview" style="margin-bottom: 30px;">
                        <div class="metric-card">
                            <div class="metric-value" id="total-tweets">--</div>
                            <div class="metric-label">Total Tweets (7j)</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="total-engagement">--</div>
                            <div class="metric-label">Engagement Total</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="avg-engagement">--</div>
                            <div class="metric-label">Engagement Moyen</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="growth-trend">--</div>
                            <div class="metric-label">Tendance Croissance</div>
                        </div>
                    </div>
                    
                    <!-- Top Performing Tweets -->
                    <div class="config-section" style="max-width: none; margin-bottom: 20px;">
                        <h3>🏆 Tweets les Plus Performants</h3>
                        <div class="form-group" style="display: flex; gap: 10px; margin-bottom: 20px;">
                            <select id="performance-days" onchange="refreshPerformance()">
                                <option value="7">7 derniers jours</option>
                                <option value="30" selected>30 derniers jours</option>
                                <option value="90">90 derniers jours</option>
                            </select>
                            <select id="performance-limit" onchange="refreshPerformance()">
                                <option value="5">Top 5</option>
                                <option value="10" selected>Top 10</option>
                                <option value="20">Top 20</option>
                            </select>
                        </div>
                        <div id="top-tweets-container" style="max-height: 600px; overflow-y: auto;">
                            <div style="text-align: center; padding: 40px; color: #64748b;">
                                🔄 Chargement des données de performance...
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="config" class="tab-content">
                <div class="config-sections">
                    <div class="section-header">
                        <h2>🔧 Configuration du Bot</h2>
                        <button class="btn" onclick="saveConfig()">💾 Sauvegarder</button>
                    </div>
                    
                    <div class="config-grid">
                        <!-- Section Posting -->
                        <div class="config-section">
                            <h3>📅 Publication</h3>
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="posting_enabled"> Activer les publications automatiques
                                </label>
                            </div>
                            <div class="form-group">
                                <label>Publications par jour:</label>
                                <input type="number" id="frequency_per_day" min="1" max="20" />
                            </div>
                            <div class="form-group">
                                <label>Heure de début:</label>
                                <input type="time" id="start_time" />
                            </div>
                            <div class="form-group">
                                <label>Heure de fin:</label>
                                <input type="time" id="end_time" />
                            </div>
                            <div class="form-group">
                                <label>Fuseau horaire:</label>
                                <select id="timezone">
                                    <option value="Asia/Bangkok">Asia/Bangkok</option>
                                    <option value="Europe/Paris">Europe/Paris</option>
                                    <option value="America/New_York">America/New_York</option>
                                    <option value="UTC">UTC</option>
                                </select>
                            </div>
                        </div>
                        
                        <!-- Section Engagement -->
                        <div class="config-section">
                            <h3>💝 Engagement</h3>
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="auto_reply_enabled"> Réponses automatiques
                                </label>
                            </div>
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="auto_like_replies"> Like automatique des réponses
                                </label>
                            </div>
                            <div class="form-group">
                                <label>Réponses max par jour:</label>
                                <input type="number" id="max_replies_per_day" min="1" max="100" />
                            </div>
                            <div class="form-group">
                                <label>Réponses max par conversation:</label>
                                <input type="number" id="max_replies_per_conversation" min="1" max="5" />
                            </div>
                            <div class="form-group">
                                <label>Intervalle de vérification (min):</label>
                                <input type="number" id="reply_check_interval" min="1" max="60" />
                            </div>
                        </div>
                        
                        <!-- Section IA -->
                        <div class="config-section">
                            <h3>🤖 Intelligence Artificielle</h3>
                            <div class="form-group">
                                <label>Fournisseur IA:</label>
                                <select id="ai_provider">
                                    <option value="auto">Automatique</option>
                                    <option value="openai">OpenAI</option>
                                    <option value="lmstudio">LM Studio</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Modèle principal:</label>
                                <input type="text" id="ai_model" placeholder="gpt-4o-mini" />
                            </div>
                            <div class="form-group">
                                <label>Température (créativité):</label>
                                <input type="range" id="temperature" min="0" max="1" step="0.1" />
                                <span id="temperature_value">0.7</span>
                            </div>
                            <div class="form-group">
                                <label>Tokens max:</label>
                                <input type="number" id="max_tokens" min="50" max="500" />
                            </div>
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="enable_images"> Génération d'images
                                </label>
                            </div>
                        </div>
                        
                        <!-- Section Types de Tweets -->
                        <div class="config-section">
                            <h3>📝 Types de Tweets</h3>
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="tweet_types_enabled"> Activer l'alternance de types
                                </label>
                            </div>
                            <div class="form-group">
                                <label>Pattern de rotation:</label>
                                <select id="rotation_pattern" multiple size="3">
                                    <option value="powerful_statement">📢 Déclaration Percutante</option>
                                    <option value="educational_post">📚 Post Éducatif</option>
                                    <option value="personal_story">👤 Histoire Personnelle</option>
                                </select>
                                <small style="color: #94a3b8;">Sélectionnez et ordonnez les types (Ctrl+clic)</small>
                            </div>
                            <div class="form-group">
                                <label>Type par défaut:</label>
                                <select id="fallback_type">
                                    <option value="powerful_statement">Déclaration Percutante</option>
                                    <option value="educational_post">Post Éducatif</option>
                                    <option value="personal_story">Histoire Personnelle</option>
                                </select>
                            </div>
                        </div>
                        
                        <!-- Section Monitoring -->
                        <div class="config-section">
                            <h3>📊 Monitoring</h3>
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="collect_stats"> Collecte des statistiques
                                </label>
                            </div>
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="daily_report"> Rapport quotidien
                                </label>
                            </div>
                            <div class="form-group">
                                <label>Heure du rapport:</label>
                                <input type="time" id="report_time" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="prompts" class="tab-content">
                <div class="config-sections">
                    <div class="section-header">
                        <h2>💬 Configuration des Prompts</h2>
                        <button class="btn" onclick="saveConfig()">💾 Sauvegarder</button>
                    </div>
                    
                    <div class="prompts-grid">
                        <div class="prompt-section">
                            <h3>📝 Génération de Tweets</h3>
                            <div class="form-group">
                                <label>Prompt système:</label>
                                <textarea id="tweet_system_prompt" rows="4" placeholder="Instructions pour la génération de tweets..."></textarea>
                            </div>
                            <div class="form-group">
                                <label>Template utilisateur:</label>
                                <textarea id="tweet_user_template" rows="3" placeholder="Template: Generate a tweet about {{topic}}..."></textarea>
                            </div>
                        </div>
                        
                        <div class="prompt-section">
                            <h3>💬 Réponses Automatiques</h3>
                            <div class="form-group">
                                <label>Prompt système:</label>
                                <textarea id="reply_system_prompt" rows="4" placeholder="Instructions pour les réponses..."></textarea>
                            </div>
                            <div class="form-group">
                                <label>Template utilisateur:</label>
                                <textarea id="reply_user_template" rows="3" placeholder="Template: Reply to @{{username}}..."></textarea>
                            </div>
                        </div>
                        
                        <div class="prompt-section">
                            <h3>🎨 Génération d'Images</h3>
                            <div class="form-group">
                                <label>Prompt de base:</label>
                                <textarea id="image_base_prompt" rows="2" placeholder="Style d'image par défaut..."></textarea>
                            </div>
                            <div class="form-group">
                                <label>Suffixe de style:</label>
                                <textarea id="image_style_suffix" rows="2" placeholder="Style artistique..."></textarea>
                            </div>
                        </div>
                        
                        <div class="prompt-section">
                            <h3>🏷️ Mots-clés Viraux</h3>
                            <div class="form-group">
                                <label>Mots-clés (un par ligne):</label>
                                <textarea id="viral_keywords" rows="8" placeholder="crypto\nsolana\nblockchain\n..."></textarea>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="test" class="tab-content">
                <div class="config-sections">
                    <div class="section-header">
                        <h2>🧪 Test des Types de Tweets</h2>
                        <button class="btn" onclick="loadTweetTypesInfo()">🔄 Actualiser Info</button>
                    </div>
                    
                    <div class="test-sections">
                        <!-- Informations sur les types -->
                        <div class="config-section">
                            <h3>ℹ️ Configuration Actuelle</h3>
                            <div id="types-info-container">
                                <div style="text-align: center; padding: 20px; color: #64748b;">
                                    🔄 Chargement des informations...
                                </div>
                            </div>
                        </div>
                        
                        <!-- Test de génération -->
                        <div class="config-section">
                            <h3>🎯 Test de Génération</h3>
                            <div class="form-group">
                                <label>Type de tweet à tester:</label>
                                <select id="test-tweet-type">
                                    <option value="powerful_statement">📢 Déclaration Percutante</option>
                                    <option value="educational_post">📚 Post Éducatif</option>
                                    <option value="personal_story">👤 Histoire Personnelle</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <button class="btn" onclick="generateTestTweet()">🎲 Générer Tweet Test</button>
                            </div>
                            <div id="test-result-container" style="margin-top: 20px;">
                                <!-- Résultats des tests -->
                            </div>
                        </div>
                        
                        <!-- Tweets Viraux d'Inspiration -->
                        <div class="config-section">
                            <h3>🔥 Tweets Viraux d'Inspiration</h3>
                            <div class="form-group">
                                <button class="btn" onclick="loadViralTweets()">🔍 Collecter Tweets Viraux</button>
                                <select id="viral-limit" style="margin-left: 10px;">
                                    <option value="5">5 tweets</option>
                                    <option value="10" selected>10 tweets</option>
                                    <option value="15">15 tweets</option>
                                    <option value="20">20 tweets</option>
                                </select>
                            </div>
                            <div id="viral-tweets-container">
                                <div style="text-align: center; padding: 20px; color: #64748b;">
                                    Cliquez sur "Collecter Tweets Viraux" pour voir l'inspiration
                                </div>
                            </div>
                        </div>
                        
                        <!-- Historique des tests -->
                        <div class="config-section">
                            <h3>📋 Historique des Tests</h3>
                            <div id="test-history-container">
                                <div style="text-align: center; padding: 20px; color: #64748b;">
                                    Aucun test généré pour le moment
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let currentConfig = null;
            let currentPrompts = null;
            
            function showTab(tabName) {{
                document.querySelectorAll('.tab-content').forEach(content => {{
                    content.classList.remove('active');
                }});
                
                document.querySelectorAll('.tab').forEach(tab => {{
                    tab.classList.remove('active');
                }});
                
                document.getElementById(tabName).classList.add('active');
                event.target.classList.add('active');
                
                // Charger la config au premier affichage
                if ((tabName === 'config' || tabName === 'prompts') && !currentConfig) {{
                    loadConfiguration();
                }}
                
                // Charger les données de performance
                if (tabName === 'performance') {{
                    refreshPerformance();
                }}
                
                // Charger les informations de test
                if (tabName === 'test') {{
                    loadTweetTypesInfo();
                }}
                
                // Sauvegarder l'onglet actif
                localStorage.setItem('activeTab', tabName);
            }}
            
            async function refreshData() {{
                try {{
                    const response = await fetch('/api/metrics');
                    const data = await response.json();
                    
                    if (data.success) {{
                        const metrics = data.data;
                        document.getElementById('status').textContent = metrics.status;
                        document.getElementById('uptime').textContent = metrics.uptime;
                        document.getElementById('tweets').textContent = metrics.tweets_today;
                        document.getElementById('likes').textContent = metrics.likes_today;
                    }}
                }} catch (error) {{
                    console.error('Erreur refresh:', error);
                }}
            }}
            
            async function loadConfiguration() {{
                try {{
                    const response = await fetch('/api/config');
                    const data = await response.json();
                    
                    if (data.success) {{
                        currentConfig = data.data.config;
                        currentPrompts = data.data.prompts;
                        populateConfigForm();
                        populatePromptsForm();
                    }} else {{
                        console.error('Erreur chargement config:', data.error);
                    }}
                }} catch (error) {{
                    console.error('Erreur chargement config:', error);
                }}
            }}
            
            function populateConfigForm() {{
                if (!currentConfig) return;
                
                // Section Posting
                const posting = currentConfig.posting || {{}};
                document.getElementById('posting_enabled').checked = posting.enabled !== false;
                document.getElementById('frequency_per_day').value = posting.frequency_per_day || 3;
                document.getElementById('start_time').value = posting.time_range?.start || '09:00';
                document.getElementById('end_time').value = posting.time_range?.end || '21:00';
                document.getElementById('timezone').value = posting.timezone || 'Asia/Bangkok';
                
                // Section Engagement
                const engagement = currentConfig.engagement || {{}};
                document.getElementById('auto_reply_enabled').checked = engagement.auto_reply_enabled === true;
                document.getElementById('auto_like_replies').checked = engagement.auto_like_replies !== false;
                document.getElementById('max_replies_per_day').value = engagement.max_replies_per_day || 20;
                document.getElementById('max_replies_per_conversation').value = engagement.max_replies_per_conversation || 1;
                document.getElementById('reply_check_interval').value = engagement.reply_check_interval_minutes || 1;
                
                // Section IA
                const content = currentConfig.content_generation || {{}};
                document.getElementById('ai_provider').value = content.provider || 'auto';
                document.getElementById('ai_model').value = content.model || 'gpt-4o-mini';
                document.getElementById('temperature').value = content.temperature || 0.7;
                document.getElementById('temperature_value').textContent = content.temperature || 0.7;
                document.getElementById('max_tokens').value = content.max_tokens || 150;
                document.getElementById('enable_images').checked = content.enable_images !== false;
                
                // Section Types de Tweets
                const tweetTypes = content.tweet_types || {{}};
                document.getElementById('tweet_types_enabled').checked = tweetTypes.enabled === true;
                document.getElementById('fallback_type').value = tweetTypes.fallback_type || 'powerful_statement';
                
                // Pattern de rotation
                const rotationPattern = tweetTypes.rotation_pattern || ['powerful_statement', 'educational_post', 'personal_story'];
                const patternSelect = document.getElementById('rotation_pattern');
                Array.from(patternSelect.options).forEach(option => {{
                    option.selected = rotationPattern.includes(option.value);
                }});
                
                // État initial des contrôles
                const isTypesEnabled = tweetTypes.enabled === true;
                ['rotation_pattern', 'fallback_type'].forEach(id => {{
                    const element = document.getElementById(id);
                    element.disabled = !isTypesEnabled;
                    element.style.opacity = isTypesEnabled ? '1' : '0.5';
                }});
                
                // Section Monitoring
                const monitoring = currentConfig.monitoring || {{}};
                document.getElementById('collect_stats').checked = monitoring.collect_stats !== false;
                document.getElementById('daily_report').checked = monitoring.daily_report !== false;
                document.getElementById('report_time').value = monitoring.report_time || '08:00';
                
                // Événement température
                document.getElementById('temperature').addEventListener('input', function() {{
                    document.getElementById('temperature_value').textContent = this.value;
                }});
                
                // Événement types de tweets
                document.getElementById('tweet_types_enabled').addEventListener('change', function() {{
                    const isEnabled = this.checked;
                    ['rotation_pattern', 'fallback_type'].forEach(id => {{
                        const element = document.getElementById(id);
                        element.disabled = !isEnabled;
                        element.style.opacity = isEnabled ? '1' : '0.5';
                    }});
                }});
            }}
            
            function populatePromptsForm() {{
                if (!currentPrompts) return;
                
                const systemPrompts = currentPrompts.system_prompts || {{}};
                const userPrompts = currentPrompts.user_prompts || {{}};
                const imagePrompts = currentPrompts.image_generation || {{}};
                
                // Prompts système
                document.getElementById('tweet_system_prompt').value = systemPrompts.tweet_generation?.content || '';
                document.getElementById('reply_system_prompt').value = systemPrompts.auto_reply?.content || '';
                
                // Templates utilisateur
                document.getElementById('tweet_user_template').value = userPrompts.tweet_generation?.template || '';
                document.getElementById('reply_user_template').value = userPrompts.auto_reply?.template || '';
                
                // Prompts images
                document.getElementById('image_base_prompt').value = imagePrompts.base_prompt || '';
                document.getElementById('image_style_suffix').value = imagePrompts.style_suffix || '';
                
                // Mots-clés viraux
                const keywords = currentConfig?.content_generation?.viral_keywords || [];
                document.getElementById('viral_keywords').value = keywords.join('\\n');
            }}
            
            async function saveConfig() {{
                try {{
                    // Construire la config depuis le formulaire
                    const configData = {{
                        config: {{
                            ...currentConfig,
                            posting: {{
                                enabled: document.getElementById('posting_enabled').checked,
                                frequency_per_day: parseInt(document.getElementById('frequency_per_day').value),
                                time_range: {{
                                    start: document.getElementById('start_time').value,
                                    end: document.getElementById('end_time').value
                                }},
                                timezone: document.getElementById('timezone').value
                            }},
                            engagement: {{
                                ...currentConfig.engagement,
                                auto_reply_enabled: document.getElementById('auto_reply_enabled').checked,
                                auto_like_replies: document.getElementById('auto_like_replies').checked,
                                max_replies_per_day: parseInt(document.getElementById('max_replies_per_day').value),
                                max_replies_per_conversation: parseInt(document.getElementById('max_replies_per_conversation').value),
                                reply_check_interval_minutes: parseInt(document.getElementById('reply_check_interval').value)
                            }},
                            content_generation: {{
                                ...currentConfig.content_generation,
                                provider: document.getElementById('ai_provider').value,
                                model: document.getElementById('ai_model').value,
                                temperature: parseFloat(document.getElementById('temperature').value),
                                max_tokens: parseInt(document.getElementById('max_tokens').value),
                                enable_images: document.getElementById('enable_images').checked,
                                viral_keywords: document.getElementById('viral_keywords').value.split('\\n').filter(k => k.trim()),
                                tweet_types: {{
                                    enabled: document.getElementById('tweet_types_enabled').checked,
                                    rotation_pattern: Array.from(document.getElementById('rotation_pattern').selectedOptions).map(opt => opt.value),
                                    fallback_type: document.getElementById('fallback_type').value,
                                    types: currentConfig.content_generation?.tweet_types?.types || {{
                                        powerful_statement: {{
                                            name: "Déclaration Percutante",
                                            description: "Une courte déclaration qui provoque une réaction",
                                            max_tokens: 100,
                                            temperature: 0.8,
                                            weight: 1,
                                            enabled: true
                                        }},
                                        educational_post: {{
                                            name: "Post Éducatif",
                                            description: "Un message détaillé et instructif",
                                            max_tokens: 280,
                                            temperature: 0.7,
                                            weight: 1,
                                            enabled: true
                                        }},
                                        personal_story: {{
                                            name: "Histoire Personnelle",
                                            description: "Une histoire personnelle et relatante",
                                            max_tokens: 250,
                                            temperature: 0.9,
                                            weight: 1,
                                            enabled: true
                                        }}
                                    }}
                                }}
                            }},
                            monitoring: {{
                                ...currentConfig.monitoring,
                                collect_stats: document.getElementById('collect_stats').checked,
                                daily_report: document.getElementById('daily_report').checked,
                                report_time: document.getElementById('report_time').value
                            }}
                        }},
                        prompts: {{
                            ...currentPrompts,
                            system_prompts: {{
                                ...currentPrompts.system_prompts,
                                tweet_generation: {{
                                    role: 'system',
                                    content: document.getElementById('tweet_system_prompt').value
                                }},
                                auto_reply: {{
                                    role: 'system',
                                    content: document.getElementById('reply_system_prompt').value
                                }}
                            }},
                            user_prompts: {{
                                ...currentPrompts.user_prompts,
                                tweet_generation: {{
                                    template: document.getElementById('tweet_user_template').value,
                                    variables: ['topic', 'style']
                                }},
                                auto_reply: {{
                                    template: document.getElementById('reply_user_template').value,
                                    variables: ['reply_content', 'username']
                                }}
                            }},
                            image_generation: {{
                                base_prompt: document.getElementById('image_base_prompt').value,
                                style_suffix: document.getElementById('image_style_suffix').value
                            }}
                        }}
                    }};
                    
                    const response = await fetch('/api/config/save', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(configData)
                    }});
                    
                    const result = await response.json();
                    
                    if (result.success) {{
                        alert('✅ Configuration sauvegardée avec succès !');
                        currentConfig = configData.config;
                        currentPrompts = configData.prompts;
                    }} else {{
                        alert('❌ Erreur lors de la sauvegarde: ' + result.error);
                    }}
                }} catch (error) {{
                    console.error('Erreur sauvegarde:', error);
                    alert('❌ Erreur de communication: ' + error.message);
                }}
            }}
            
            async function refreshPerformance() {{
                try {{
                    const days = document.getElementById('performance-days').value;
                    const limit = document.getElementById('performance-limit').value;
                    
                    // Charger l'aperçu des performances
                    const overviewResponse = await fetch(`/api/stats/performance-overview?days=7`);
                    const overviewData = await overviewResponse.json();
                    
                    if (overviewData.success) {{
                        const overview = overviewData.data;
                        document.getElementById('total-tweets').textContent = overview.total_tweets;
                        document.getElementById('total-engagement').textContent = overview.total_engagement;
                        document.getElementById('avg-engagement').textContent = overview.avg_engagement_per_tweet;
                        
                        const trendElement = document.getElementById('growth-trend');
                        const trend = overview.growth_trend;
                        if (trend > 0) {{
                            trendElement.textContent = `+${{trend}}%`;
                            trendElement.style.color = '#10b981';
                        }} else if (trend < 0) {{
                            trendElement.textContent = `${{trend}}%`;
                            trendElement.style.color = '#ef4444';
                        }} else {{
                            trendElement.textContent = '0%';
                            trendElement.style.color = '#64748b';
                        }}
                    }}
                    
                    // Charger les top tweets
                    const tweetsResponse = await fetch(`/api/stats/top-tweets?days=${{days}}&limit=${{limit}}`);
                    const tweetsData = await tweetsResponse.json();
                    
                    if (tweetsData.success) {{
                        displayTopTweets(tweetsData.data);
                    }} else {{
                        document.getElementById('top-tweets-container').innerHTML = 
                            '<div style="text-align: center; padding: 40px; color: #ef4444;">❌ Erreur de chargement des données</div>';
                    }}
                }} catch (error) {{
                    console.error('Erreur refresh performance:', error);
                    document.getElementById('top-tweets-container').innerHTML = 
                        '<div style="text-align: center; padding: 40px; color: #ef4444;">❌ Erreur de connexion</div>';
                }}
            }}
            
            function displayTopTweets(tweets) {{
                const container = document.getElementById('top-tweets-container');
                
                if (!tweets || tweets.length === 0) {{
                    container.innerHTML = '<div style="text-align: center; padding: 40px; color: #64748b;">📭 Aucune donnée de performance disponible</div>';
                    return;
                }}
                
                const tweetsHtml = tweets.map((tweet, index) => {{
                    const date = new Date(tweet.posted_at).toLocaleDateString('fr-FR', {{
                        day: '2-digit',
                        month: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit'
                    }});
                    
                    const engagementBadge = tweet.engagement_score > 100 ? '🔥' : 
                                          tweet.engagement_score > 50 ? '⭐' : 
                                          tweet.engagement_score > 20 ? '👍' : '📊';
                    
                    return `
                        <div style="background: #334155; border-radius: 8px; padding: 15px; margin-bottom: 15px; border-left: 4px solid ${{index < 3 ? '#f59e0b' : '#64748b'}};">
                            <div style="display: flex; justify-content: between; align-items: flex-start; margin-bottom: 10px;">
                                <div style="flex: 1;">
                                    <div style="font-weight: bold; color: #f1f5f9; margin-bottom: 5px;">
                                        ${{engagementBadge}} #${{index + 1}} - Score: ${{tweet.engagement_score}}
                                    </div>
                                    <div style="color: #94a3b8; font-size: 12px;">${{date}}</div>
                                </div>
                                <a href="${{tweet.tweet_url}}" target="_blank" style="background: #3b82f6; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-size: 12px;">
                                    🔗 Voir Tweet
                                </a>
                            </div>
                            
                            <div style="color: #e2e8f0; margin-bottom: 15px; line-height: 1.4;">
                                ${{tweet.content}}
                            </div>
                            
                            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; font-size: 14px;">
                                <div style="text-align: center; background: #475569; padding: 8px; border-radius: 4px;">
                                    <div style="color: #f472b6; font-weight: bold;">${{tweet.likes}}</div>
                                    <div style="color: #94a3b8; font-size: 12px;">❤️ Likes</div>
                                </div>
                                <div style="text-align: center; background: #475569; padding: 8px; border-radius: 4px;">
                                    <div style="color: #22d3ee; font-weight: bold;">${{tweet.retweets}}</div>
                                    <div style="color: #94a3b8; font-size: 12px;">🔄 Retweets</div>
                                </div>
                                <div style="text-align: center; background: #475569; padding: 8px; border-radius: 4px;">
                                    <div style="color: #a78bfa; font-weight: bold;">${{tweet.replies}}</div>
                                    <div style="color: #94a3b8; font-size: 12px;">💬 Réponses</div>
                                </div>
                                <div style="text-align: center; background: #475569; padding: 8px; border-radius: 4px;">
                                    <div style="color: #fbbf24; font-weight: bold;">${{tweet.impressions || 'N/A'}}</div>
                                    <div style="color: #94a3b8; font-size: 12px;">👁️ Vues</div>
                                </div>
                            </div>
                        </div>
                    `;
                }}).join('');
                
                container.innerHTML = tweetsHtml;
            }}
            
            async function collectStatsNow() {{
                try {{
                    const button = event.target;
                    const originalText = button.textContent;
                    button.textContent = '⏳ Collecte...';
                    button.disabled = true;
                    
                    const response = await fetch('/api/stats/collect-now', {{
                        method: 'POST'
                    }});
                    const data = await response.json();
                    
                    if (data.success) {{
                        alert('✅ Collecte de stats déclenchée avec succès !');
                        // Actualiser les données après 5 secondes
                        setTimeout(() => {{
                            refreshPerformance();
                        }}, 5000);
                    }} else {{
                        alert('❌ Erreur lors de la collecte: ' + data.error);
                    }}
                    
                    button.textContent = originalText;
                    button.disabled = false;
                }} catch (error) {{
                    console.error('Erreur collecte stats:', error);
                    alert('❌ Erreur de communication: ' + error.message);
                    event.target.textContent = '🔄 Collecter Stats';
                    event.target.disabled = false;
                }}
            }}
            
            let testHistory = [];
            
            async function loadTweetTypesInfo() {{
                try {{
                    const response = await fetch('/api/test/tweet-types');
                    const data = await response.json();
                    
                    if (data.success) {{
                        displayTweetTypesInfo(data.data);
                    }} else {{
                        document.getElementById('types-info-container').innerHTML = 
                            '<div style="text-align: center; padding: 20px; color: #ef4444;">❌ Erreur de chargement</div>';
                    }}
                }} catch (error) {{
                    console.error('Erreur chargement types info:', error);
                    document.getElementById('types-info-container').innerHTML = 
                        '<div style="text-align: center; padding: 20px; color: #ef4444;">❌ Erreur de connexion</div>';
                }}
            }}
            
            function displayTweetTypesInfo(typesData) {{
                const container = document.getElementById('types-info-container');
                
                const statusBadge = typesData.enabled ? 
                    '<span style="background: #10b981; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">✅ Activé</span>' :
                    '<span style="background: #ef4444; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">❌ Désactivé</span>';
                
                const typesHtml = typesData.types.map(type => {{
                    const enabledBadge = type.enabled ? '✅' : '❌';
                    return `
                        <div style="background: #475569; border-radius: 6px; padding: 15px; margin: 10px 0;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <h4 style="margin: 0; color: #f1f5f9;">${{type.name}} ${{enabledBadge}}</h4>
                                <div style="font-size: 12px; color: #94a3b8;">
                                    Tokens: ${{type.max_tokens}} | Temp: ${{type.temperature}}
                                </div>
                            </div>
                            <p style="margin: 0; color: #cbd5e1; font-size: 14px;">${{type.description}}</p>
                        </div>
                    `;
                }}).join('');
                
                const rotationInfo = typesData.rotation_pattern.length > 0 ? 
                    typesData.rotation_pattern.map(type => {{
                        const typeInfo = typesData.types.find(t => t.key === type);
                        return typeInfo ? typeInfo.name : type;
                    }}).join(' → ') : 'Aucun pattern défini';
                
                container.innerHTML = `
                    <div style="margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <h4 style="margin: 0; color: #f1f5f9;">Statut du Système</h4>
                            ${{statusBadge}}
                        </div>
                        <div style="background: #334155; border-radius: 6px; padding: 15px;">
                            <div style="margin-bottom: 10px;">
                                <strong style="color: #e2e8f0;">Pattern de Rotation:</strong>
                                <div style="color: #94a3b8; margin-top: 5px;">${{rotationInfo}}</div>
                            </div>
                            <div>
                                <strong style="color: #e2e8f0;">Type par Défaut:</strong>
                                <span style="color: #94a3b8; margin-left: 10px;">${{typesData.fallback_type}}</span>
                            </div>
                        </div>
                    </div>
                    <div>
                        <h4 style="margin-bottom: 15px; color: #f1f5f9;">Types de Tweets Configurés</h4>
                        ${{typesHtml}}
                    </div>
                `;
            }}
            
            async function generateTestTweet() {{
                try {{
                    const button = event.target;
                    const originalText = button.textContent;
                    button.textContent = '⏳ Génération...';
                    button.disabled = true;
                    
                    const tweetType = document.getElementById('test-tweet-type').value;
                    
                    const response = await fetch('/api/test/generate-tweet', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ type: tweetType }})
                    }});
                    
                    const data = await response.json();
                    
                    if (data.success) {{
                        const result = data.data;
                        displayTestResult(result);
                        addToTestHistory(result);
                        updateTestHistory();
                    }} else {{
                        displayTestError(data.error);
                    }}
                    
                    button.textContent = originalText;
                    button.disabled = false;
                }} catch (error) {{
                    console.error('Erreur génération test:', error);
                    displayTestError('Erreur de connexion: ' + error.message);
                    event.target.textContent = '🎲 Générer Tweet Test';
                    event.target.disabled = false;
                }}
            }}
            
            function displayTestResult(result) {{
                const container = document.getElementById('test-result-container');
                
                const lengthColor = result.length > 250 ? '#ef4444' : result.length > 200 ? '#f59e0b' : '#10b981';
                const lengthIcon = result.length > 250 ? '⚠️' : result.length > 200 ? '⚡' : '✅';
                
                container.innerHTML = `
                    <div style="background: #334155; border-radius: 8px; padding: 20px; border-left: 4px solid #10b981;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <h4 style="margin: 0; color: #f1f5f9;">✅ ${{result.type_name}}</h4>
                            <div style="display: flex; gap: 10px; font-size: 12px;">
                                <span style="background: #475569; padding: 4px 8px; border-radius: 4px; color: #cbd5e1;">
                                    Tokens: ${{result.max_tokens}}
                                </span>
                                <span style="background: #475569; padding: 4px 8px; border-radius: 4px; color: #cbd5e1;">
                                    Temp: ${{result.temperature}}
                                </span>
                                <span style="background: ${{lengthColor}}; padding: 4px 8px; border-radius: 4px; color: white;">
                                    ${{lengthIcon}} ${{result.length}}/280
                                </span>
                            </div>
                        </div>
                        
                        <div style="background: #1e293b; border-radius: 6px; padding: 15px; margin-bottom: 15px;">
                            <div style="color: #e2e8f0; line-height: 1.5; font-size: 16px;">
                                ${{result.content}}
                            </div>
                        </div>
                        
                        <div style="color: #94a3b8; font-size: 14px; font-style: italic;">
                            ${{result.type_description}}
                        </div>
                    </div>
                `;
            }}
            
            function displayTestError(error) {{
                const container = document.getElementById('test-result-container');
                container.innerHTML = `
                    <div style="background: #7f1d1d; border-radius: 8px; padding: 20px; border-left: 4px solid #ef4444;">
                        <h4 style="margin: 0 0 10px 0; color: #fecaca;">❌ Erreur de Génération</h4>
                        <div style="color: #f87171;">${{error}}</div>
                    </div>
                `;
            }}
            
            function addToTestHistory(result) {{
                const historyItem = {{
                    ...result,
                    timestamp: new Date().toLocaleString('fr-FR'),
                    id: Date.now()
                }};
                testHistory.unshift(historyItem);
                
                // Garder seulement les 10 derniers tests
                if (testHistory.length > 10) {{
                    testHistory = testHistory.slice(0, 10);
                }}
            }}
            
            function updateTestHistory() {{
                const container = document.getElementById('test-history-container');
                
                if (testHistory.length === 0) {{
                    container.innerHTML = '<div style="text-align: center; padding: 20px; color: #64748b;">Aucun test généré pour le moment</div>';
                    return;
                }}
                
                const historyHtml = testHistory.map((item, index) => {{
                    const lengthColor = item.length > 250 ? '#ef4444' : item.length > 200 ? '#f59e0b' : '#10b981';
                    
                    return `
                        <div style="background: #475569; border-radius: 6px; padding: 15px; margin-bottom: 10px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <div style="font-weight: bold; color: #f1f5f9;">${{item.type_name}}</div>
                                <div style="display: flex; gap: 10px; font-size: 12px;">
                                    <span style="color: #94a3b8;">${{item.timestamp}}</span>
                                    <span style="color: ${{lengthColor}};">${{item.length}}/280</span>
                                </div>
                            </div>
                            <div style="color: #cbd5e1; font-size: 14px; line-height: 1.4;">
                                ${{item.content.length > 100 ? item.content.substring(0, 100) + '...' : item.content}}
                            </div>
                        </div>
                    `;
                }}).join('');
                
                container.innerHTML = historyHtml;
            }}
            
            async function loadViralTweets() {{
                try {{
                    const button = event.target;
                    const originalText = button.textContent;
                    button.textContent = '⏳ Collecte...';
                    button.disabled = true;
                    
                    const limit = document.getElementById('viral-limit').value;
                    
                    const response = await fetch(`/api/viral-tweets?limit=${{limit}}`);
                    const data = await response.json();
                    
                    if (data.success) {{
                        displayViralTweets(data.data);
                    }} else {{
                        displayViralError(data.error);
                    }}
                    
                    button.textContent = originalText;
                    button.disabled = false;
                }} catch (error) {{
                    console.error('Erreur collecte tweets viraux:', error);
                    displayViralError('Erreur de connexion: ' + error.message);
                    event.target.textContent = '🔍 Collecter Tweets Viraux';
                    event.target.disabled = false;
                }}
            }}
            
            function displayViralTweets(data) {{
                const container = document.getElementById('viral-tweets-container');
                
                if (!data.tweets || data.tweets.length === 0) {{
                    container.innerHTML = `
                        <div style="text-align: center; padding: 20px; color: #f59e0b;">
                            🤷‍♂️ ${{data.message || 'Aucun tweet viral trouvé'}}
                        </div>
                    `;
                    return;
                }}
                
                // Statistiques globales
                const analysis = data.analysis || {{}};
                const statsHtml = `
                    <div style="background: #334155; border-radius: 6px; padding: 15px; margin-bottom: 20px;">
                        <h4 style="margin: 0 0 10px 0; color: #f1f5f9;">📊 Analyse de la Collection</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; font-size: 14px;">
                            <div style="background: #475569; padding: 10px; border-radius: 4px; text-align: center;">
                                <div style="color: #fbbf24; font-weight: bold; font-size: 18px;">${{data.total_found}}</div>
                                <div style="color: #94a3b8;">Tweets collectés</div>
                            </div>
                            <div style="background: #475569; padding: 10px; border-radius: 4px; text-align: center;">
                                <div style="color: #22d3ee; font-weight: bold; font-size: 18px;">${{Math.round(analysis.avg_length || 0)}}</div>
                                <div style="color: #94a3b8;">Longueur moyenne</div>
                            </div>
                            <div style="background: #475569; padding: 10px; border-radius: 4px; text-align: center;">
                                <div style="color: #a78bfa; font-weight: bold; font-size: 18px;">${{Math.round(analysis.avg_virality || 0)}}</div>
                                <div style="color: #94a3b8;">Score viral moyen</div>
                            </div>
                            <div style="background: #475569; padding: 10px; border-radius: 4px; text-align: center;">
                                <div style="color: #10b981; font-weight: bold; font-size: 18px;">${{analysis.with_hashtags || 0}}</div>
                                <div style="color: #94a3b8;">Avec hashtags</div>
                            </div>
                        </div>
                    </div>
                `;
                
                // Tweets individuels
                const tweetsHtml = data.tweets.map((tweet, index) => {{
                    const viralityColor = tweet.virality_score > 80 ? '#f59e0b' : 
                                        tweet.virality_score > 50 ? '#a78bfa' : '#64748b';
                    const viralityIcon = tweet.virality_score > 80 ? '🔥' : 
                                       tweet.virality_score > 50 ? '⭐' : '📊';
                    
                    const topicsHtml = tweet.topics.length > 0 ? 
                        tweet.topics.map(topic => `<span style="background: #475569; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-right: 5px;">${{topic}}</span>`).join('') : 
                        '<span style="color: #64748b; font-size: 11px;">Aucun topic détecté</span>';
                    
                    const styleIndicators = [];
                    if (tweet.has_hashtags) styleIndicators.push('🏷️ Hashtags');
                    if (tweet.has_mentions) styleIndicators.push('👤 Mentions');
                    if (tweet.has_emoji) styleIndicators.push('😀 Emojis');
                    
                    return `
                        <div style="background: #1e293b; border-radius: 8px; padding: 15px; margin-bottom: 15px; border-left: 4px solid ${{viralityColor}};">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                                <div style="flex: 1;">
                                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 5px;">
                                        <span style="background: ${{viralityColor}}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                                            ${{viralityIcon}} Score: ${{tweet.virality_score}}
                                        </span>
                                        <span style="color: #94a3b8; font-size: 12px;">
                                            ${{tweet.length}} caractères
                                        </span>
                                    </div>
                                    <div style="margin-bottom: 8px;">
                                        ${{topicsHtml}}
                                    </div>
                                </div>
                            </div>
                            
                            <div style="background: #334155; border-radius: 6px; padding: 12px; margin-bottom: 12px;">
                                <div style="color: #e2e8f0; line-height: 1.4; font-size: 15px; white-space: pre-wrap;">
                                    ${{tweet.text}}
                                </div>
                            </div>
                            
                            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px;">
                                <div style="color: #94a3b8;">
                                    ${{styleIndicators.join(' • ')}}
                                </div>
                                <div style="color: #64748b;">
                                    #${{index + 1}}
                                </div>
                            </div>
                        </div>
                    `;
                }}).join('');
                
                container.innerHTML = statsHtml + tweetsHtml;
            }}
            
            function displayViralError(error) {{
                const container = document.getElementById('viral-tweets-container');
                container.innerHTML = `
                    <div style="background: #7f1d1d; border-radius: 8px; padding: 20px; border-left: 4px solid #ef4444;">
                        <h4 style="margin: 0 0 10px 0; color: #fecaca;">❌ Erreur de Collecte</h4>
                        <div style="color: #f87171;">${{error}}</div>
                    </div>
                `;
            }}
            
            refreshData();
            setInterval(refreshData, {refresh_interval});
            
            // Charger les données de performance quand l'onglet Performance est affiché
            if (window.location.hash === '#performance' || localStorage.getItem('activeTab') === 'performance') {{
                refreshPerformance();
            }}
        </script>
    </body>
    </html>
    """
    
    return html_content 