# Requirements Document

## Introduction

AI Besin Asistanı, mevcut fitness takip uygulamasına entegre edilecek yeni bir özelliktir. Bu özellik, kullanıcıların mevcut besin veritabanında bulunmayan yiyecekler için besin değerlerini öğrenmelerine yardımcı olacak bir yapay zeka asistanı sağlar. Sistem, ücretsiz/yerel AI modelleri kullanarak Türkçe dilinde hizmet verecek ve mevcut glassmorphism tasarım diliyle tutarlı modern bir kullanıcı arayüzüne sahip olacaktır.

## Glossary

- **AI_Assistant**: Besin değerleri hakkında bilgi sağlayan yapay zeka asistanı sistemi
- **Food_Database**: Mevcut diyetkolik.com'dan çekilen besin öğeleri veritabanı
- **Nutrition_Query**: Kullanıcının besin değerleri hakkında sorduğu soru
- **Local_AI_Model**: Ücretsiz ve yerel olarak çalışan yapay zeka modeli
- **Glassmorphism_UI**: Mevcut uygulamada kullanılan cam efektli tasarım dili
- **Food_Search_System**: Mevcut manuel besin arama ve girme sistemi
- **Turkish_Language**: Asistanın hizmet vereceği ana dil
- **Nutrition_Information**: Kalori, protein, karbonhidrat, yağ gibi besin değerleri bilgileri
- **Chat_Interface**: Kullanıcı ile AI asistanı arasındaki sohbet arayüzü
- **Response_Parser**: AI yanıtlarından besin değerlerini çıkaran sistem bileşeni
- **Automatic_Food_Discovery**: Veritabanında olmayan besinleri otomatik olarak bulan ve ekleyen sistem
- **Web_Scraping_Engine**: Türk besin sitelerinden veri çeken scraping motoru
- **Smart_Food_Prediction**: AI destekli besin değeri tahmin sistemi
- **Database_Auto_Expansion**: Bulunan yeni besinleri otomatik veritabanına ekleyen sistem

## Requirements

### Requirement 1: AI Assistant Integration

**User Story:** As a fitness app user, I want to access an AI nutrition assistant, so that I can get nutrition information for foods not in the existing database.

#### Acceptance Criteria

1. THE AI_Assistant SHALL be accessible as a new menu item in the existing sidebar navigation
2. WHEN a user clicks the AI assistant menu item, THE System SHALL display the chat interface
3. THE Chat_Interface SHALL maintain consistency with the existing Glassmorphism_UI design
4. THE AI_Assistant SHALL integrate seamlessly alongside the existing Food_Search_System without replacing it
5. THE System SHALL use only Local_AI_Model instances that require no paid API subscriptions

### Requirement 2: Turkish Language Support

**User Story:** As a Turkish-speaking user, I want the AI assistant to communicate in Turkish, so that I can easily understand and interact with the system.

#### Acceptance Criteria

1. THE AI_Assistant SHALL respond to all queries in Turkish_Language
2. THE Chat_Interface SHALL display all UI elements and labels in Turkish_Language
3. WHEN a user enters a query in Turkish, THE AI_Assistant SHALL understand and process it correctly
4. THE AI_Assistant SHALL provide nutrition information using Turkish food names and terminology
5. THE System SHALL handle Turkish character encoding (ç, ğ, ı, ö, ş, ü) correctly in all interactions

### Requirement 3: Nutrition Information Retrieval

**User Story:** As a user, I want to ask about nutrition values of foods, so that I can get detailed nutritional information for meal planning.

#### Acceptance Criteria

1. WHEN a user submits a Nutrition_Query, THE AI_Assistant SHALL provide calories per 100g information
2. WHEN a user submits a Nutrition_Query, THE AI_Assistant SHALL provide protein per 100g information
3. WHEN a user submits a Nutrition_Query, THE AI_Assistant SHALL provide carbohydrate per 100g information
4. WHEN a user submits a Nutrition_Query, THE AI_Assistant SHALL provide fat per 100g information
5. THE AI_Assistant SHALL format Nutrition_Information in a structured, readable format
6. WHEN nutrition information is unavailable, THE AI_Assistant SHALL provide a clear explanation and suggest alternatives

### Requirement 4: Chat Interface Implementation

**User Story:** As a user, I want to interact with the AI assistant through a chat interface, so that I can have natural conversations about nutrition.

#### Acceptance Criteria

1. THE Chat_Interface SHALL display a conversation history with user messages and AI responses
2. THE Chat_Interface SHALL include a text input field for typing nutrition queries
3. THE Chat_Interface SHALL include a send button to submit queries
4. WHEN a user sends a message, THE System SHALL display a loading indicator while processing
5. THE Chat_Interface SHALL auto-scroll to show the latest messages
6. THE Chat_Interface SHALL persist conversation history during the user session
7. THE System SHALL clear conversation history when the user navigates away from the page

### Requirement 5: Local AI Model Integration

**User Story:** As a system administrator, I want the AI assistant to use free local models, so that there are no ongoing API costs or external dependencies.

#### Acceptance Criteria

1. THE System SHALL use only Local_AI_Model instances that can run without internet connectivity
2. THE Local_AI_Model SHALL be capable of understanding Turkish nutrition queries
3. THE System SHALL not make any calls to paid external AI APIs (OpenAI, Claude, etc.)
4. WHEN the Local_AI_Model is unavailable, THE System SHALL display an appropriate error message
5. THE System SHALL initialize the Local_AI_Model during application startup
6. THE Local_AI_Model SHALL respond to queries within 10 seconds under normal conditions

### Requirement 6: Response Processing and Parsing

**User Story:** As a user, I want AI responses to be properly formatted, so that I can easily read and understand the nutrition information.

#### Acceptance Criteria

1. THE Response_Parser SHALL extract structured nutrition data from AI responses
2. WHEN the AI provides nutrition values, THE Response_Parser SHALL identify calories, protein, carbs, and fat values
3. THE System SHALL display nutrition information in a card format consistent with existing food log displays
4. WHEN nutrition values are provided, THE System SHALL validate that they are reasonable (calories 0-900 per 100g, macros 0-100g per 100g)
5. IF parsed nutrition values are unreasonable, THEN THE System SHALL display the raw AI response instead of structured data

### Requirement 7: Integration with Existing Food System

**User Story:** As a user, I want to add AI-suggested nutrition information to my food log, so that I can track foods not in the database.

#### Acceptance Criteria

1. WHEN the AI provides structured nutrition information, THE System SHALL display an "Add to Food Log" button
2. WHEN a user clicks "Add to Food Log", THE System SHALL pre-populate the food entry form with AI-provided data
3. THE System SHALL allow users to edit AI-suggested values before adding to their log
4. THE System SHALL redirect users to the food log page after adding an AI-suggested food
5. THE System SHALL store AI-suggested foods as manual entries (not linked to Food_Database items)

### Requirement 8: User Interface Design Consistency

**User Story:** As a user, I want the AI assistant interface to match the existing app design, so that I have a consistent user experience.

#### Acceptance Criteria

1. THE Chat_Interface SHALL use the same GlassCard components as other pages
2. THE Chat_Interface SHALL use the same color scheme and typography as the existing application
3. THE Chat_Interface SHALL be responsive and work properly on mobile devices
4. THE Chat_Interface SHALL use the same button styles and input field designs as existing forms
5. THE Chat_Interface SHALL include appropriate loading states and animations consistent with the app

### Requirement 9: Error Handling and User Feedback

**User Story:** As a user, I want clear feedback when something goes wrong, so that I understand what happened and what to do next.

#### Acceptance Criteria

1. WHEN the Local_AI_Model fails to respond, THE System SHALL display a user-friendly error message in Turkish
2. WHEN a user submits an empty query, THE System SHALL display a validation message
3. WHEN the AI response cannot be parsed, THE System SHALL display the raw response with a note about manual interpretation
4. THE System SHALL provide retry functionality when AI requests fail
5. THE System SHALL log errors for debugging while showing user-friendly messages to users

### Requirement 10: Performance and Resource Management

**User Story:** As a user, I want the AI assistant to respond quickly, so that I can efficiently get nutrition information.

#### Acceptance Criteria

1. THE System SHALL limit conversation history to the last 50 messages to manage memory usage
2. THE Local_AI_Model SHALL be optimized for nutrition-related queries to improve response accuracy
3. THE System SHALL implement request queuing to handle multiple simultaneous queries gracefully
4. THE Chat_Interface SHALL remain responsive during AI processing
5. THE System SHALL provide progress indicators for requests taking longer than 3 seconds

### Requirement 11: Automatic Food Discovery and Database Expansion

**User Story:** As a user, I want the AI assistant to automatically find and learn about foods not in the database, so that I can get nutrition information for any food I ask about.

#### Acceptance Criteria

1. WHEN a food is not found in the local database, THE Automatic_Food_Discovery SHALL search multiple external sources automatically
2. THE Web_Scraping_Engine SHALL search Turkish nutrition websites (diyetkolik.com, beslenme.gov.tr) for missing foods
3. THE System SHALL use multiple free nutrition APIs (USDA, OpenFoodFacts, Edamam) as fallback sources
4. WHEN no exact match is found, THE Smart_Food_Prediction SHALL estimate nutrition values based on similar foods and ingredients
5. THE Database_Auto_Expansion SHALL automatically add newly discovered foods to the local database with user confirmation
6. THE System SHALL assign confidence scores to all discovered nutrition data (high/medium/low)
7. WHEN multiple sources provide conflicting data, THE System SHALL use weighted averaging based on source reliability
8. THE System SHALL cache discovered foods for 30 days to improve performance for repeated queries
9. THE System SHALL provide source attribution for all discovered nutrition data
10. THE System SHALL allow users to report incorrect nutrition data for quality improvement