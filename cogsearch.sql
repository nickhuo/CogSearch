CREATE DATABASE IF NOT EXISTS `cogsearch_textsearch3` DEFAULT CHARACTER SET latin1 COLLATE latin1_swedish_ci;
USE `cogsearch_textsearch3`;

-- --------------------------------------------------------

--
-- Table structure for table `output1_url`
--

DROP TABLE IF EXISTS `output1_url`;
CREATE TABLE `output1_url` (
  `op1ID` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `sid` varchar(100) NOT NULL,
  `topID` varchar(8) NOT NULL,
  `subtopID` varchar(8) NOT NULL,
  `conID` varchar(8) NOT NULL,
  `passID` varchar(8) NOT NULL,
  `pageTypeID` varchar(40) NOT NULL,
  `time_stamp` varchar(50) NOT NULL,
  `unixTime` int(10) NOT NULL,
  `time_interval` int(11) NOT NULL,
  `url` varchar(100) NOT NULL,
  `pageTitle` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;


DROP TABLE IF EXISTS `tb1_user`;
CREATE TABLE `tb1_user` (
  `uid` int(11) NOT NULL,
  `sid` varchar(100) NOT NULL,
  `topIDorder` varchar(20) DEFAULT NULL,
  `subtopIDorder` varchar(20) NOT NULL,
  `conIDorder` varchar(30) NOT NULL,
  `taskDone` int(11) NOT NULL,
  `conDone` int(11) NOT NULL,
  `signedConsent` varchar(8) NOT NULL,
  `signedDate` varchar(50) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;


DROP TABLE IF EXISTS `tb2_topic`;
CREATE TABLE `tb2_topic` (
  `topID` varchar(8) NOT NULL,
  `topTitle` varchar(100) NOT NULL,
  `topIdeasBonusWords` longtext NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb3_subtopic`;
CREATE TABLE `tb3_subtopic` (
  `subtopID` varchar(8) NOT NULL,
  `topID` varchar(8) NOT NULL,
  `subtopTitle` varchar(100) NOT NULL,
  `subtopQuesOne` text NOT NULL,
  `subtopAnsOne` varchar(10) NOT NULL,
  `subtopQuesTwo` text NOT NULL,
  `subtopAnsTwo` varchar(10) NOT NULL,
  `subtopQuesThr` text NOT NULL,
  `subtopAnsThr` varchar(10) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb4_passage`;
CREATE TABLE `tb4_passage` (
  `topID` varchar(8) NOT NULL,
  `subtopID` varchar(8) NOT NULL,
  `conID` varchar(8) NOT NULL,
  `passID` varchar(8) NOT NULL,
  `passOrder` varchar(100) NOT NULL,
  `passTitle` varchar(100) NOT NULL,
  `passText` longtext NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb5_passQop`;
CREATE TABLE `tb5_passQop` (
  `tb5id` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `sid` varchar(100) NOT NULL,
  `topID` varchar(8) NOT NULL,
  `subtopID` varchar(8) NOT NULL,
  `conID` varchar(8) NOT NULL,
  `passID` varchar(8) NOT NULL,
  `passOrder` varchar(4) NOT NULL,
  `c1Ans` int(11) NOT NULL,
  `c2Ans` int(11) NOT NULL DEFAULT 0,
  `c3Ans` int(11) NOT NULL DEFAULT 0,
  `passRT` int(11) NOT NULL DEFAULT 0
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb6_taskTime`;
CREATE TABLE `tb6_taskTime` (
  `tb6id` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `sid` varchar(100) NOT NULL,
  `topID` varchar(8) NOT NULL,
  `timeStart` int(10) NOT NULL,
  `timeEnd` int(10) NOT NULL,
  `timeStartStamp` varchar(50) NOT NULL,
  `timeEndStamp` varchar(50) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb7_topicSummary`;
CREATE TABLE `tb7_topicSummary` (
  `tb7id` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `sid` varchar(100) NOT NULL,
  `topID` varchar(8) NOT NULL,
  `quesID` varchar(8) NOT NULL,
  `quesAns` longtext NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb8_topicIdeas`;
CREATE TABLE `tb8_topicIdeas` (
  `tb8id` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `sid` varchar(100) NOT NULL,
  `topID` varchar(8) NOT NULL,
  `quesID` varchar(8) NOT NULL,
  `quesAns` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb9_topicBonus`;
CREATE TABLE `tb9_topicBonus` (
  `tb9id` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `sid` varchar(100) NOT NULL,
  `topID` varchar(8) NOT NULL,
  `quesID` varchar(8) NOT NULL,
  `quesAns` longtext NOT NULL,
  `bonusWord` longtext NOT NULL,
  `bonusWordCnt` int(11) NOT NULL DEFAULT 0,
  `bonusMoney` decimal(20,2) NOT NULL DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb10_subtopQos`;
CREATE TABLE `tb10_subtopQos` (
  `tb10id` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `sid` varchar(100) NOT NULL,
  `topID` varchar(8) NOT NULL,
  `subtopID` varchar(8) NOT NULL,
  `conID` varchar(8) NOT NULL,
  `pageTypeID` varchar(8) NOT NULL,
  `quesAns1` varchar(10) NOT NULL,
  `quesAns2` varchar(10) NOT NULL,
  `quesAns3` varchar(10) NOT NULL,
  `subtopScore` decimal(10,1) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb11_profile`;
CREATE TABLE `tb11_profile` (
  `tb11id` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `sid` varchar(100) NOT NULL,
  `dobMonth` varchar(4) NOT NULL,
  `dobDay` varchar(4) NOT NULL,
  `dobYear` varchar(8) NOT NULL,
  `dobSum` varchar(20) NOT NULL,
  `age` varchar(4) NOT NULL,
  `gender` varchar(2) NOT NULL,
  `edu` varchar(8) NOT NULL,
  `natEng` varchar(2) NOT NULL,
  `firLan` varchar(100) NOT NULL,
  `ageEng` varchar(4) NOT NULL,
  `hisLat` varchar(2) NOT NULL,
  `race` varchar(2) NOT NULL,
  `lc1` varchar(2) NOT NULL DEFAULT '',
  `lc2` varchar(2) NOT NULL DEFAULT '',
  `lc3` varchar(2) NOT NULL DEFAULT '',
  `lc4` varchar(2) NOT NULL DEFAULT '',
  `lc5` varchar(2) NOT NULL DEFAULT '',
  `lc6` varchar(2) NOT NULL DEFAULT '',
  `lc7` varchar(2) NOT NULL DEFAULT '',
  `lc8` varchar(2) NOT NULL DEFAULT '',
  `lc9` varchar(2) NOT NULL DEFAULT '',
  `lc10` varchar(2) NOT NULL DEFAULT '',
  `lcOneScore` decimal(10,1) NOT NULL DEFAULT 0.0,
  `lcOneRT` int(11) NOT NULL DEFAULT 0,
  `lc11` varchar(2) NOT NULL DEFAULT '',
  `lc12` varchar(2) NOT NULL DEFAULT '',
  `lc13` varchar(2) NOT NULL DEFAULT '',
  `lc14` varchar(2) NOT NULL DEFAULT '',
  `lc15` varchar(2) NOT NULL DEFAULT '',
  `lc16` varchar(2) NOT NULL DEFAULT '',
  `lc17` varchar(2) NOT NULL DEFAULT '',
  `lc18` varchar(2) NOT NULL DEFAULT '',
  `lc19` varchar(2) NOT NULL DEFAULT '',
  `lc20` varchar(2) NOT NULL DEFAULT '',
  `lcTwoScore` decimal(10,1) NOT NULL DEFAULT 0.0,
  `lcTwoRT` int(11) NOT NULL DEFAULT 0,
  `voc1` varchar(2) NOT NULL DEFAULT '',
  `voc2` varchar(2) NOT NULL DEFAULT '',
  `voc3` varchar(2) NOT NULL DEFAULT '',
  `voc4` varchar(2) NOT NULL DEFAULT '',
  `voc5` varchar(2) NOT NULL DEFAULT '',
  `voc6` varchar(2) NOT NULL DEFAULT '',
  `voc7` varchar(2) NOT NULL DEFAULT '',
  `voc8` varchar(2) NOT NULL DEFAULT '',
  `voc9` varchar(2) NOT NULL DEFAULT '',
  `voc10` varchar(2) NOT NULL DEFAULT '',
  `voc11` varchar(2) NOT NULL DEFAULT '',
  `voc12` varchar(2) NOT NULL DEFAULT '',
  `voc13` varchar(2) NOT NULL DEFAULT '',
  `voc14` varchar(2) NOT NULL DEFAULT '',
  `voc15` varchar(2) NOT NULL DEFAULT '',
  `vocScore` decimal(10,1) NOT NULL DEFAULT 0.0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb12_prac_topic`;
CREATE TABLE `tb12_prac_topic` (
  `topID` varchar(8) NOT NULL,
  `topTitle` varchar(100) NOT NULL,
  `topIdeasBonusWords` longtext NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb13_prac_subtopic`;
CREATE TABLE `tb13_prac_subtopic` (
  `subtopID` varchar(8) NOT NULL,
  `topID` varchar(8) NOT NULL,
  `subtopTitle` varchar(100) NOT NULL,
  `subtopQuesOne` text NOT NULL,
  `subtopAnsOne` varchar(10) NOT NULL,
  `subtopQuesTwo` text NOT NULL,
  `subtopAnsTwo` varchar(10) NOT NULL,
  `subtopQuesThr` text NOT NULL,
  `subtopAnsThr` varchar(10) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb14_prac_passage`;
CREATE TABLE `tb14_prac_passage` (
  `topID` varchar(8) NOT NULL,
  `subtopID` varchar(8) NOT NULL,
  `conID` varchar(8) NOT NULL,
  `passID` varchar(8) NOT NULL,
  `passOrder` varchar(4) NOT NULL,
  `passTitle` varchar(100) NOT NULL,
  `passText` longtext NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb15_prac_passQop`;
CREATE TABLE `tb15_prac_passQop` (
  `tb15id` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `sid` varchar(100) NOT NULL,
  `topID` varchar(8) NOT NULL,
  `subtopID` varchar(8) NOT NULL,
  `conID` varchar(8) NOT NULL,
  `passID` varchar(8) NOT NULL,
  `passOrder` varchar(4) NOT NULL,
  `c1Ans` int(11) NOT NULL,
  `c2Ans` int(11) NOT NULL,
  `c3Ans` int(11) NOT NULL,
  `passRT` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb16_prac_taskTime`;
CREATE TABLE `tb16_prac_taskTime` (
  `tb16id` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `sid` varchar(100) NOT NULL,
  `topID` varchar(8) NOT NULL,
  `timeStart` int(10) NOT NULL,
  `timeEnd` int(10) NOT NULL,
  `timeStartStamp` varchar(50) NOT NULL,
  `timeEndStamp` varchar(50) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb17_prac_topicSummary`;
CREATE TABLE `tb17_prac_topicSummary` (
  `tb17id` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `sid` varchar(100) NOT NULL,
  `topID` varchar(8) NOT NULL,
  `quesID` varchar(8) NOT NULL,
  `quesAns` longtext NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb18_prac_topicIdeas`;
CREATE TABLE `tb18_prac_topicIdeas` (
  `tb18id` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `sid` varchar(100) NOT NULL,
  `topID` varchar(8) NOT NULL,
  `quesID` varchar(8) NOT NULL,
  `quesAns` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb19_prac_topicBonus`;
CREATE TABLE `tb19_prac_topicBonus` (
  `tb19id` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `sid` varchar(100) NOT NULL,
  `topID` varchar(8) NOT NULL,
  `quesID` varchar(8) NOT NULL,
  `quesAns` longtext NOT NULL,
  `bonusWord` longtext NOT NULL,
  `bonusWordCnt` int(11) NOT NULL DEFAULT 0,
  `bonusMoney` decimal(20,2) NOT NULL DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb20_prac_subtopQos`;
CREATE TABLE `tb20_prac_subtopQos` (
  `tb20id` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `sid` varchar(100) NOT NULL,
  `topID` varchar(8) NOT NULL,
  `subtopID` varchar(8) NOT NULL,
  `conID` varchar(8) NOT NULL,
  `pageTypeID` varchar(8) NOT NULL,
  `quesAns1` varchar(10) NOT NULL,
  `quesAns2` varchar(10) NOT NULL,
  `quesAns3` varchar(10) NOT NULL,
  `subtopScore` decimal(10,1) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

DROP TABLE IF EXISTS `tb21_questions`;
CREATE TABLE `tb21_questions` (
  `questionID` varchar(233) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `passID` varchar(8) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `topID` varchar(8) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `subtopID` varchar(8) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `conID` varchar(8) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `passOrder` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `passTitle` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `questionText` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `choiceA` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `choiceB` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `choiceC` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `choiceD` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `correctAns` varchar(10) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

DROP TABLE IF EXISTS `tb22_multiQop`;
CREATE TABLE `tb22_multiQop` (
  `tb22id` int(11) NOT NULL,
  `uid` int(11) NOT NULL,
  `sid` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `questionID` varchar(8) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `topID` varchar(8) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `subtopID` varchar(8) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `conID` varchar(8) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `passID` varchar(8) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `passOrder` varchar(4) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `choice` varchar(4) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `isCorrect` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
