-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: mysql-fyp-fypdb.c.aivencloud.com    Database: defaultdb
-- ------------------------------------------------------
-- Server version	8.4.11

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '3423c9fb-d0a4-11f1-b360-1a7d3163f2d2:1-66,
64b9a126-d2bf-11f1-b188-8636e5cf6492:1-29';

--
-- Table structure for table `attempts`
--

DROP TABLE IF EXISTS `attempts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attempts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `module_id` int NOT NULL,
  `score` int NOT NULL,
  `difficulty` varchar(10) NOT NULL,
  `context` varchar(30) NOT NULL DEFAULT 'general',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `module_id` (`module_id`),
  CONSTRAINT `attempts_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `attempts_ibfk_2` FOREIGN KEY (`module_id`) REFERENCES `modules` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `attempts`
--

LOCK TABLES `attempts` WRITE;
/*!40000 ALTER TABLE `attempts` DISABLE KEYS */;
/*!40000 ALTER TABLE `attempts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `modules`
--

DROP TABLE IF EXISTS `modules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `modules` (
  `id` int NOT NULL AUTO_INCREMENT,
  `slug` varchar(50) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `slug` (`slug`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `modules`
--

LOCK TABLES `modules` WRITE;
/*!40000 ALTER TABLE `modules` DISABLE KEYS */;
INSERT INTO `modules` VALUES (1,'social-engineering-phishing','Social Engineering & Phishing','Spot manipulation tactics, fake emails, texts and chat messages'),(2,'bank-scams','Bank & payment scams','Spot fraudulent banking contact and fake offers'),(3,'malware','Malware','Spot fake alerts, downloads and attachments'),(4,'password-security','Passwords & account security','Protect your accounts');
/*!40000 ALTER TABLE `modules` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recovery_codes`
--

DROP TABLE IF EXISTS `recovery_codes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recovery_codes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `code_hash` varchar(255) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `recovery_codes_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recovery_codes`
--

LOCK TABLES `recovery_codes` WRITE;
/*!40000 ALTER TABLE `recovery_codes` DISABLE KEYS */;
INSERT INTO `recovery_codes` VALUES (17,4,'scrypt:32768:8:1$lNmk0FZNSmH6UuhH$bec6db466196e5b428b120300305d47bf0c4cf1209ba2a252b7347b6d8e65b39a272f78356b1875a361342ccc3ac5869fe0bac194a24f119cbec7f8ab12af0ae','2026-10-28 15:45:47'),(18,4,'scrypt:32768:8:1$xfrPMvSeKGeLQPrg$270edf142c9d89d1ec76903e75bfd780ba59e9fc3e9250ae48539d9903f91e7727051266531f80fdb157a7ff6de127abb508b18dcd4cbe1465d84bb745352655','2026-10-28 15:45:47'),(19,4,'scrypt:32768:8:1$Chc8AsGine2glt7B$106539b62178494bc960f5db4eda67adb39c2fa26254773926015ae767458f70ab27e6077ddeb81b0396c10d5129b2c22af597fab10acd87035d202f2ab889db','2026-10-28 15:45:47'),(20,4,'scrypt:32768:8:1$ed3vlbvJryMpJJ3Q$2ba1733adc230e22511a2dd2df17504814697890014fd355e8d2add878e44b654884624081051c700a6d5bfda7d9cd392dc98cf420fd98c4a5950cd7a0bc5956','2026-10-28 15:45:48'),(21,4,'scrypt:32768:8:1$4ipVzN34QikuA4uu$6c3f0663b6bc7e6351474fb78d7cdecb66623d413fc5479260c5b94e94aaa42bba7141fb5a76e6931b591fb277f8db288802bd798bc4e001d54c23b34ab8af5f','2026-10-28 15:45:48'),(22,4,'scrypt:32768:8:1$qBqQCPlO8fX5BaE9$7a1ff9634f9fb0c2a3dd50a612b693698974cc1bab6a24242c1b7754a3fc12d992e5315dea7e4e50920b0833cdeee90c01056c91142aea43ca417d05271784c6','2026-10-28 15:45:48'),(23,4,'scrypt:32768:8:1$Pd1R6gvtqpLOke4y$2ca89af861039f7cd8738384f94be860be3f79c2aedfcea1c888eaf291ac1821ef9a918ce31f4015a57e542a48640a9ee0d2fa92146909bce12a2a4b203953a2','2026-10-28 15:45:48'),(24,4,'scrypt:32768:8:1$rl2gAzbuGEJTQYo9$6c3a0596716220fcf6380f2ddef29ccd201a1c31b8ee6f1bd2ebafed0f5186748ac4853ae8185435ba9d54d08f03d9cc9444859e624e6d0c895142d3caebb6e7','2026-10-28 15:45:48');
/*!40000 ALTER TABLE `recovery_codes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `url_scans`
--

DROP TABLE IF EXISTS `url_scans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `url_scans` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `sample_id` int NOT NULL,
  `user_guess` varchar(10) NOT NULL,
  `result` varchar(20) NOT NULL,
  `correct` tinyint(1) NOT NULL,
  `scanned_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `url_scans_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `url_scans_chk_guess` CHECK ((`user_guess` in (_utf8mb4'threat',_utf8mb4'safe'))),
  CONSTRAINT `url_scans_chk_result` CHECK ((`result` in (_utf8mb4'malicious',_utf8mb4'suspicious',_utf8mb4'harmless',_utf8mb4'undetected')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `url_scans`
--

LOCK TABLES `url_scans` WRITE;
/*!40000 ALTER TABLE `url_scans` DISABLE KEYS */;
/*!40000 ALTER TABLE `url_scans` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `email` varchar(255) NOT NULL,
  `hashed_password` varchar(255) NOT NULL,
  `twofa_confirmed` tinyint(1) NOT NULL DEFAULT '0',
  `twofa_secret` varchar(255) NOT NULL,
  `password_reset_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (4,'testman123','testman456@gmail.com','scrypt:32768:8:1$1K5Cm6Px7IFR6k7P$52dc59dbb6ce61e4421d6b64ff7e72ce19f5d020db6d7c1eabfa0810853fb35c22a950a704130b0a7a2767665bda910a16f3ffd60ec7384193d6683a64d6667c',1,'gAAAAABq4hhepGSgh0pl29xN9VV4bFvw87W3P0E6dFMsiQTn54mhdzoMqlrXs9MCT3CdE847g1gjXj40vjLHiYcIs-A-KxHXRi_NBLK0eRQevBnS6xrtwZKcz6RXTYZRvRenqrBWjuEL',NULL),(5,'testjoe456','testjoe456@gmail.com','scrypt:32768:8:1$0fZFXzYgydrzOd7v$ee967bedc746cfe2cd7e4a37b3479ae16817e8e1c0a28e71c2b6825de9678cd8c8dd524f1c1a69ea8f17910ce17c03ba4b5817933ed8675d54bc9f2f5c505e1a',0,'gAAAAABq4h7eBagXgXaviZskM2JkmnYLFKjZLU5Hk11Et69MmNuoM_hVU0xwsQSqdjo4_3OLDtbpRVq0llWzcU2u2Sw8rBPj1J3R1IeQahMiiSCwmXDSEiXJ7T5YGKRfeR07GFEDxE27',NULL);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-03 17:35:55
