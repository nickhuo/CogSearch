-- Seed Data for CogSearch Database
-- This file contains mock data for testing the application
-- Run this after creating the database with schema.sql

USE `cogsearch_textsearch3`;

-- Disable foreign key checks for data insertion
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================================
-- Core Topic and Content Data
-- ============================================================================

-- Insert topics for main tasks
INSERT INTO `tb2_topic` (`topID`, `topTitle`, `topIdeasBonusWords`) VALUES
('1', 'Climate Change and Environmental Science', 'greenhouse effect,carbon footprint,renewable energy,sustainability,biodiversity,ecosystem,pollution,global warming,conservation,deforestation'),
('2', 'Artificial Intelligence and Technology', 'machine learning,neural networks,algorithm,automation,data science,robotics,computer vision,natural language processing,deep learning,artificial intelligence'),
('3', 'Health and Medical Research', 'vaccine,immunology,clinical trial,diagnosis,treatment,medicine,healthcare,disease,prevention,therapy');

-- Insert subtopics
INSERT INTO `tb3_subtopic` (`subtopID`, `topID`, `subtopTitle`, `subtopQuesOne`, `subtopAnsOne`, `subtopQuesTwo`, `subtopAnsTwo`, `subtopQuesThr`, `subtopAnsThr`) VALUES
('1', '1', 'Global Warming Effects', 'What is the primary cause of global warming?', 'greenhouse', 'What gas is most responsible for climate change?', 'carbon', 'What type of energy reduces carbon emissions?', 'renewable'),
('2', '1', 'Ocean Acidification', 'What happens when oceans absorb CO2?', 'acidify', 'What marine life is most affected by acidification?', 'coral', 'What is the pH trend in oceans?', 'decreasing'),
('3', '1', 'Renewable Energy Solutions', 'What energy source uses wind?', 'turbines', 'What energy comes from the sun?', 'solar', 'What energy uses water flow?', 'hydro'),
('1', '2', 'Machine Learning Basics', 'What type of learning uses labeled data?', 'supervised', 'What learns without labeled data?', 'unsuper', 'What learns through trial and error?', 'reinforce'),
('2', '2', 'Neural Networks', 'What mimics brain neurons in AI?', 'neural', 'What connects neural layers?', 'weights', 'What function activates neurons?', 'activation'),
('3', '2', 'Natural Language Processing', 'What processes human language?', 'NLP', 'What converts speech to text?', 'ASR', 'What generates human text?', 'GPT'),
('1', '3', 'Vaccine Development', 'What provides immunity against diseases?', 'vaccine', 'What tests drug safety and efficacy?', 'trials', 'What approves new medicines?', 'FDA'),
('2', '3', 'Disease Prevention', 'What prevents disease spread?', 'hygiene', 'What builds community immunity?', 'vaccine', 'What tracks disease outbreaks?', 'tracking'),
('3', '3', 'Medical Diagnostics', 'What uses images to diagnose?', 'radiology', 'What analyzes blood samples?', 'lab', 'What examines tissue samples?', 'biopsy');

-- Insert passages for each subtopic
INSERT INTO `tb4_passage` (`topID`, `subtopID`, `conID`, `passID`, `passOrder`, `passTitle`, `passText`) VALUES
-- Climate Change passages
('1', '1', '1', '1011001', '1', 'The Greenhouse Effect Explained', 'The greenhouse effect is a natural process that warms the Earth''s surface. When the Sun''s energy reaches the Earth''s atmosphere, some of it is reflected back to space and the rest is absorbed and re-radiated by greenhouse gases. Greenhouse gases include water vapor, carbon dioxide, methane, nitrous oxide, and ozone. These gases trap heat in the atmosphere, keeping Earth warm enough to sustain life. However, human activities have dramatically increased the concentration of these gases, particularly carbon dioxide from burning fossil fuels, leading to enhanced global warming.'),
('1', '1', '1', '1011002', '2', 'Rising Sea Levels', 'Global warming causes sea level rise through two main mechanisms: thermal expansion of seawater and increased melting of land-based ice. As ocean temperatures rise, water expands, contributing to higher sea levels. Additionally, warming temperatures accelerate the melting of glaciers and ice sheets in Greenland and Antarctica. These changes threaten coastal communities worldwide, with some island nations facing complete submersion. Scientists predict that sea levels could rise by 1-2 meters by 2100 if current warming trends continue.'),
('1', '2', '1', '1021001', '1', 'Ocean Chemistry Changes', 'Ocean acidification occurs when seawater absorbs carbon dioxide from the atmosphere. The CO2 dissolves in seawater, forming carbonic acid, which lowers the ocean''s pH. Since the Industrial Revolution, ocean pH has dropped by 0.1 units, representing a 30% increase in acidity. This change affects marine ecosystems, particularly organisms that build calcium carbonate shells or skeletons, such as corals, mollusks, and some plankton. The impacts cascade through the marine food web, affecting fish populations and ocean biodiversity.'),
('1', '3', '1', '1031001', '1', 'Solar Energy Revolution', 'Solar photovoltaic technology has experienced dramatic cost reductions and efficiency improvements over the past decade. Modern solar panels can convert over 20% of sunlight into electricity, and costs have fallen by more than 80% since 2010. Solar farms now generate electricity at costs competitive with fossil fuels in many regions. Innovations in energy storage, such as lithium-ion batteries, are solving the intermittency challenge, allowing solar power to provide electricity even when the sun isn''t shining. Many countries are rapidly expanding their solar capacity as part of renewable energy transitions.'),
-- AI passages
('2', '1', '1', '2011001', '1', 'Supervised Learning Fundamentals', 'Supervised learning is a machine learning approach where algorithms learn from labeled training data to make predictions on new, unseen data. The algorithm analyzes input-output pairs to discover patterns and relationships. Common examples include email spam detection, image recognition, and medical diagnosis. The quality and quantity of training data directly affect model performance. Key algorithms include decision trees, random forests, support vector machines, and neural networks. Cross-validation techniques help evaluate model performance and prevent overfitting to training data.'),
('2', '2', '1', '2021001', '1', 'Deep Neural Networks', 'Deep neural networks are computing systems inspired by biological neural networks. They consist of multiple layers of interconnected nodes (neurons) that process and transform data. Each connection has an associated weight that adjusts during training through backpropagation. Deep networks can automatically learn hierarchical representations of data, making them powerful for tasks like image recognition, natural language processing, and game playing. Recent architectures like transformers and attention mechanisms have revolutionized many AI applications.'),
('2', '3', '1', '2031001', '1', 'Language Model Evolution', 'Natural Language Processing has evolved from rule-based systems to statistical models to modern transformer architectures. Large language models like GPT (Generative Pre-trained Transformer) are trained on vast amounts of text data to understand and generate human-like language. These models can perform various tasks including translation, summarization, question answering, and creative writing. The attention mechanism allows models to focus on relevant parts of input text, dramatically improving performance on complex language understanding tasks.'),
-- Health passages
('3', '1', '1', '3011001', '1', 'Vaccine Development Process', 'Vaccine development follows a rigorous multi-phase process to ensure safety and efficacy. Preclinical research involves laboratory and animal studies to test initial safety and immune response. Phase I trials test safety in small groups of humans. Phase II trials expand to hundreds of participants to further evaluate safety and immune response. Phase III trials involve thousands of participants to test efficacy against the target disease. After regulatory approval, Phase IV surveillance continues to monitor long-term effects. The entire process typically takes 10-15 years, though emergency situations can accelerate timelines.'),
('3', '2', '1', '3021001', '1', 'Public Health Strategies', 'Disease prevention relies on multiple complementary strategies. Primary prevention aims to prevent disease before it occurs through vaccination, healthy lifestyle promotion, and environmental improvements. Secondary prevention focuses on early detection through screening programs to catch diseases in treatable stages. Tertiary prevention manages existing diseases to prevent complications and improve quality of life. Population-level interventions like clean water systems, air quality regulations, and food safety standards have historically had enormous impacts on public health.'),
('3', '3', '1', '3031001', '1', 'Modern Diagnostic Techniques', 'Medical diagnostics have been revolutionized by advanced imaging and molecular techniques. Magnetic Resonance Imaging (MRI) provides detailed soft tissue images without radiation. Computed Tomography (CT) offers high-resolution cross-sectional body images. Positron Emission Tomography (PET) shows metabolic activity in tissues. Genetic sequencing can identify hereditary diseases and guide personalized treatments. Artificial intelligence is increasingly used to analyze medical images and assist in diagnosis, sometimes achieving accuracy comparable to experienced physicians.');

-- ============================================================================
-- Practice Topic and Content Data
-- ============================================================================

-- Insert practice topics
INSERT INTO `tb12_prac_topic` (`topID`, `topTitle`, `topIdeasBonusWords`) VALUES
('1', 'Basic Reading Comprehension', 'understanding,inference,main idea,supporting details,context clues,vocabulary,analysis,interpretation,summary,conclusion');

-- Insert practice subtopics
INSERT INTO `tb13_prac_subtopic` (`subtopID`, `topID`, `subtopTitle`, `subtopQuesOne`, `subtopAnsOne`, `subtopQuesTwo`, `subtopAnsTwo`, `subtopQuesThr`, `subtopAnsThr`) VALUES
('1', '1', 'Finding Main Ideas', 'What is the central theme of a paragraph?', 'main', 'What supports the main idea?', 'details', 'Where is the main idea usually found?', 'beginning'),
('2', '1', 'Understanding Context', 'What helps determine word meaning?', 'context', 'What are hints about meaning called?', 'clues', 'What skill helps with unknown words?', 'inference'),
('3', '1', 'Making Inferences', 'What is reading between the lines?', 'inference', 'What requires logical thinking?', 'reasoning', 'What is an educated guess?', 'hypothesis');

-- Insert practice passages
INSERT INTO `tb14_prac_passage` (`topID`, `subtopID`, `conID`, `passID`, `passOrder`, `passTitle`, `passText`) VALUES
('1', '1', '1', '1011001', '1', 'The Benefits of Reading', 'Reading is one of the most important skills for academic and personal success. Regular reading improves vocabulary, enhances critical thinking abilities, and expands knowledge across many subjects. Students who read frequently tend to perform better in school and develop stronger communication skills. Reading also provides entertainment and stress relief, offering an escape into different worlds and perspectives. Whether fiction or non-fiction, books expose readers to new ideas and ways of thinking that can shape their worldview.'),
('1', '2', '1', '1021001', '1', 'Urban Gardens Transform Communities', 'Community gardens are sprouting up in cities worldwide, transforming vacant lots into green spaces that benefit entire neighborhoods. These gardens provide fresh vegetables and fruits to residents, many of whom live in food deserts with limited access to healthy produce. Beyond nutrition, urban gardens create social connections as neighbors work together to tend plants and share harvests. Children learn about nature and food production, while adults find stress relief through gardening activities. The environmental benefits include improved air quality, reduced urban heat, and habitat for pollinators.'),
('1', '3', '1', '1031001', '1', 'The Digital Revolution', 'The widespread adoption of smartphones and internet connectivity has fundamentally changed how people communicate, work, and access information. While these technologies offer unprecedented convenience and global connectivity, they also present challenges. Many people struggle with information overload and difficulty focusing on single tasks. Social media platforms can create both meaningful connections and social pressures. The key to thriving in the digital age lies in developing digital literacy skills and maintaining balance between online and offline activities.');

-- ============================================================================
-- Sample Questions for Testing
-- ============================================================================

-- Insert sample questions
INSERT INTO `tb21_questions` (`questionID`, `passID`, `topID`, `subtopID`, `conID`, `passOrder`, `passTitle`, `questionText`, `choiceA`, `choiceB`, `choiceC`, `choiceD`, `correctAns`) VALUES
('Q1011001A', '1011001', '1', '1', '1', '1', 'The Greenhouse Effect Explained', 'What is the primary cause of the enhanced greenhouse effect?', 'Natural processes', 'Human activities', 'Solar radiation', 'Ocean currents', 'B'),
('Q1011001B', '1011001', '1', '1', '1', '1', 'The Greenhouse Effect Explained', 'Which gas is specifically mentioned as increasing due to fossil fuel burning?', 'Water vapor', 'Methane', 'Carbon dioxide', 'Ozone', 'C'),
('Q2011001A', '2011001', '2', '1', '1', '1', 'Supervised Learning Fundamentals', 'What type of data does supervised learning require?', 'Unlabeled data', 'Labeled training data', 'Random data', 'Synthetic data', 'B'),
('Q3011001A', '3011001', '3', '1', '1', '1', 'Vaccine Development Process', 'How long does the typical vaccine development process take?', '1-2 years', '5-7 years', '10-15 years', '20+ years', 'C');

-- Normalize passOrder to two digits to match app queries (expects '01','02',...)
UPDATE tb4_passage SET passOrder = LPAD(passOrder, 2, '0') WHERE CHAR_LENGTH(passOrder) = 1;
UPDATE tb14_prac_passage SET passOrder = LPAD(passOrder, 2, '0') WHERE CHAR_LENGTH(passOrder) = 1;

-- ============================================================================
-- Sample User Data for Testing
-- ============================================================================

-- Insert test users
INSERT INTO `tb1_user` (`sid`, `topIDorder`, `subtopIDorder`, `conIDorder`, `taskDone`, `conDone`, `signedConsent`, `signedDate`) VALUES
('TEST001', '1,2,3', '1,2,3', '1,1,1', 0, 0, 'yes', '2024-09-12 10:00:00'),
('TEST002', '2,1,3', '2,1,3', '1,1,1', 0, 0, 'yes', '2024-09-12 10:15:00'),
('DEMO001', '1', '1,2,3', '1,1,1', 0, 0, 'yes', '2024-09-12 09:30:00');

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- Verification Queries (uncomment to test)
-- ============================================================================

/*
-- Verify data insertion
SELECT 'Topics:' as table_name, COUNT(*) as record_count FROM tb2_topic
UNION ALL
SELECT 'Subtopics:', COUNT(*) FROM tb3_subtopic
UNION ALL
SELECT 'Passages:', COUNT(*) FROM tb4_passage
UNION ALL
SELECT 'Practice Topics:', COUNT(*) FROM tb12_prac_topic
UNION ALL
SELECT 'Practice Subtopics:', COUNT(*) FROM tb13_prac_subtopic
UNION ALL
SELECT 'Practice Passages:', COUNT(*) FROM tb14_prac_passage
UNION ALL
SELECT 'Questions:', COUNT(*) FROM tb21_questions
UNION ALL
SELECT 'Users:', COUNT(*) FROM tb1_user;

-- Show sample topic with subtopics
SELECT t.topID, t.topTitle, s.subtopID, s.subtopTitle 
FROM tb2_topic t 
JOIN tb3_subtopic s ON t.topID = s.topID 
WHERE t.topID = '1' 
ORDER BY s.subtopID;
*/
