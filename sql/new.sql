-- MySQL dump 10.19  Distrib 10.3.36-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: CAM-AI_LAST
-- ------------------------------------------------------
-- Server version	10.3.36-MariaDB-0+deb10u2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `access_access_control`
--

DROP TABLE IF EXISTS `access_access_control`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `access_access_control` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `vtype` varchar(1) NOT NULL,
  `vid` int(11) NOT NULL,
  `u_g` varchar(1) NOT NULL,
  `u_g_nr` int(11) NOT NULL,
  `r_w` varchar(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `access_access_control`
--

LOCK TABLES `access_access_control` WRITE;
/*!40000 ALTER TABLE `access_access_control` DISABLE KEYS */;
/*!40000 ALTER TABLE `access_access_control` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=105 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add camurl',7,'add_camurl'),(26,'Can change camurl',7,'change_camurl'),(27,'Can delete camurl',7,'delete_camurl'),(28,'Can view camurl',7,'view_camurl'),(29,'Can add setting',8,'add_setting'),(30,'Can change setting',8,'change_setting'),(31,'Can delete setting',8,'delete_setting'),(32,'Can view setting',8,'view_setting'),(33,'Can add view_log',9,'add_view_log'),(34,'Can change view_log',9,'change_view_log'),(35,'Can delete view_log',9,'delete_view_log'),(36,'Can view view_log',9,'view_view_log'),(37,'Can add stream',10,'add_stream'),(38,'Can change stream',10,'change_stream'),(39,'Can delete stream',10,'delete_stream'),(40,'Can view stream',10,'view_stream'),(41,'Can add access_control',11,'add_access_control'),(42,'Can change access_control',11,'change_access_control'),(43,'Can delete access_control',11,'delete_access_control'),(44,'Can view access_control',11,'view_access_control'),(45,'Can add event',12,'add_event'),(46,'Can change event',12,'change_event'),(47,'Can delete event',12,'delete_event'),(48,'Can view event',12,'view_event'),(49,'Can add evt_condition',13,'add_evt_condition'),(50,'Can change evt_condition',13,'change_evt_condition'),(51,'Can delete evt_condition',13,'delete_evt_condition'),(52,'Can view evt_condition',13,'view_evt_condition'),(53,'Can add event_frame',14,'add_event_frame'),(54,'Can change event_frame',14,'change_event_frame'),(55,'Can delete event_frame',14,'delete_event_frame'),(56,'Can view event_frame',14,'view_event_frame'),(57,'Can add worker',15,'add_worker'),(58,'Can change worker',15,'change_worker'),(59,'Can delete worker',15,'delete_worker'),(60,'Can view worker',15,'view_worker'),(61,'Can add school',16,'add_school'),(62,'Can change school',16,'change_school'),(63,'Can delete school',16,'delete_school'),(64,'Can view school',16,'view_school'),(65,'Can add mask',17,'add_mask'),(66,'Can change mask',17,'change_mask'),(67,'Can delete mask',17,'delete_mask'),(68,'Can view mask',17,'view_mask'),(69,'Can add fit',18,'add_fit'),(70,'Can change fit',18,'change_fit'),(71,'Can delete fit',18,'delete_fit'),(72,'Can view fit',18,'view_fit'),(73,'Can add trainer',19,'add_trainer'),(74,'Can change trainer',19,'change_trainer'),(75,'Can delete trainer',19,'delete_trainer'),(76,'Can view trainer',19,'view_trainer'),(77,'Can add trainframe',20,'add_trainframe'),(78,'Can change trainframe',20,'change_trainframe'),(79,'Can delete trainframe',20,'delete_trainframe'),(80,'Can view trainframe',20,'view_trainframe'),(81,'Can add epoch',21,'add_epoch'),(82,'Can change epoch',21,'change_epoch'),(83,'Can delete epoch',21,'delete_epoch'),(84,'Can view epoch',21,'view_epoch'),(85,'Can add tag',22,'add_tag'),(86,'Can change tag',22,'change_tag'),(87,'Can delete tag',22,'delete_tag'),(88,'Can view tag',22,'view_tag'),(89,'Can add userinfo',23,'add_userinfo'),(90,'Can change userinfo',23,'change_userinfo'),(91,'Can delete userinfo',23,'delete_userinfo'),(92,'Can view userinfo',23,'view_userinfo'),(93,'Can add archive',24,'add_archive'),(94,'Can change archive',24,'change_archive'),(95,'Can delete archive',24,'delete_archive'),(96,'Can view archive',24,'view_archive'),(97,'Can add client',25,'add_client'),(98,'Can change client',25,'change_client'),(99,'Can delete client',25,'delete_client'),(100,'Can view client',25,'view_client'),(101,'Can add client',26,'add_client'),(102,'Can change client',26,'change_client'),(103,'Can delete client',26,'delete_client'),(104,'Can view client',26,'view_client');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$320000$qNLhQwFZlSenPndPEOhpgq$JUgVnfc3Pag91aDbq5HSrKebkjBGSwJKZMWJxCYuGQU=','2022-11-22 10:22:42.839893',1,'admin','admin','admin','ludger@booker-hellerhoff.de',1,1,'2022-01-23 19:32:53.722000');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL CHECK (`action_flag` >= 0),
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2022-11-08 16:04:19.849110','1','Stream model, name: BüroCam',2,'[{\"changed\": {\"fields\": [\"Name\"]}}]',10,1),(2,'2022-11-09 11:39:00.690972','1','First School',2,'[{\"changed\": {\"fields\": [\"Name\"]}}]',16,1);
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (11,'access','access_control'),(1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(5,'contenttypes','contenttype'),(17,'drawpad','mask'),(12,'eventers','event'),(14,'eventers','event_frame'),(13,'eventers','evt_condition'),(22,'schools','tag'),(6,'sessions','session'),(10,'streams','stream'),(16,'tf_workers','school'),(15,'tf_workers','worker'),(7,'tools','camurl'),(8,'tools','setting'),(25,'trainers','client'),(21,'trainers','epoch'),(18,'trainers','fit'),(19,'trainers','trainer'),(20,'trainers','trainframe'),(24,'users','archive'),(23,'users','userinfo'),(9,'viewers','view_log'),(26,'ws_predictions','client');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_migrations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2022-11-04 18:56:57.246365'),(2,'auth','0001_initial','2022-11-04 18:56:57.532126'),(3,'admin','0001_initial','2022-11-04 18:56:57.599926'),(4,'admin','0002_logentry_remove_auto_add','2022-11-04 18:56:57.607507'),(5,'admin','0003_logentry_add_action_flag_choices','2022-11-04 18:56:57.616569'),(6,'contenttypes','0002_remove_content_type_name','2022-11-04 18:56:57.669260'),(7,'auth','0002_alter_permission_name_max_length','2022-11-04 18:56:57.725637'),(8,'auth','0003_alter_user_email_max_length','2022-11-04 18:56:57.741043'),(9,'auth','0004_alter_user_username_opts','2022-11-04 18:56:57.748792'),(10,'auth','0005_alter_user_last_login_null','2022-11-04 18:56:57.773612'),(11,'auth','0006_require_contenttypes_0002','2022-11-04 18:56:57.776596'),(12,'auth','0007_alter_validators_add_error_messages','2022-11-04 18:56:57.786986'),(13,'auth','0008_alter_user_username_max_length','2022-11-04 18:56:57.824373'),(14,'auth','0009_alter_user_last_name_max_length','2022-11-04 18:56:57.858603'),(15,'auth','0010_alter_group_name_max_length','2022-11-04 18:56:57.870261'),(16,'auth','0011_update_proxy_permissions','2022-11-04 18:56:57.879404'),(17,'auth','0012_alter_user_first_name_max_length','2022-11-04 18:56:57.918067'),(18,'trainers','0001_initial','2022-11-04 18:56:58.033282'),(19,'tf_workers','0001_initial','2022-11-04 18:56:58.114272'),(20,'streams','0001_initial','2022-11-04 18:56:58.160346'),(21,'drawpad','0001_initial','2022-11-04 18:56:58.202518'),(22,'eventers','0001_initial','2022-11-04 18:56:58.355303'),(23,'schools','0001_initial','2022-11-04 18:56:58.373325'),(24,'sessions','0001_initial','2022-11-04 18:56:58.433658'),(25,'tools','0001_initial','2022-11-04 18:56:58.461717'),(26,'users','0001_initial','2022-11-04 18:56:58.680482'),(27,'viewers','0001_initial','2022-11-04 18:56:58.693531'),(28,'access','0001_initial','2022-11-04 20:00:10.465123'),(29,'tf_workers','0002_alter_school_donate_pics_alter_school_l_rate_max_and_more','2022-11-09 15:00:42.185899'),(30,'trainers','0002_trainer_wsname_trainer_wspass_alter_trainer_t_type','2022-11-09 15:00:42.207089'),(31,'tf_workers','0003_alter_school_weight_boost_alter_worker_wsserver','2022-11-09 20:14:38.528761'),(32,'trainers','0003_alter_trainer_wsserver','2022-11-09 20:14:38.535209'),(33,'trainers','0004_client','2022-11-16 11:23:37.199017'),(34,'ws_predictions','0001_initial','2022-11-16 11:23:37.214114'),(35,'trainers','0005_client_comment','2022-11-16 11:30:51.758613'),(36,'ws_predictions','0002_client_comment','2022-11-16 11:30:51.771806'),(37,'tf_workers','0004_worker_wsadminpass','2022-11-16 11:47:03.108665'),(38,'trainers','0006_trainer_wsadminpass','2022-11-16 11:47:03.119436'),(39,'users','0002_remove_userinfo_counter_remove_userinfo_school_and_more','2022-11-16 16:32:31.594661'),(40,'users','0003_alter_userinfo_client_nr','2022-11-16 16:42:28.317011'),(41,'users','0004_remove_userinfo_client_nr','2022-11-16 16:47:30.398896'),(42,'users','0005_userinfo_client_nr','2022-11-16 16:48:21.483471'),(43,'tf_workers','0005_worker_wsid','2022-11-22 20:49:05.753087'),(44,'trainers','0007_delete_client_remove_trainer_wsadminpass','2022-11-23 14:14:26.771639');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `drawpad_mask`
--

DROP TABLE IF EXISTS `drawpad_mask`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `drawpad_mask` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `mtype` varchar(1) NOT NULL,
  `name` varchar(100) NOT NULL,
  `definition` varchar(500) NOT NULL,
  `stream_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `drawpad_mask_stream_id_c1668505_fk_streams_stream_id` (`stream_id`),
  CONSTRAINT `drawpad_mask_stream_id_c1668505_fk_streams_stream_id` FOREIGN KEY (`stream_id`) REFERENCES `streams_stream` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `drawpad_mask`
--

LOCK TABLES `drawpad_mask` WRITE;
/*!40000 ALTER TABLE `drawpad_mask` DISABLE KEYS */;
/*!40000 ALTER TABLE `drawpad_mask` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `eventers_event`
--

DROP TABLE IF EXISTS `eventers_event`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `eventers_event` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `p_string` varchar(255) NOT NULL,
  `start` datetime(6) NOT NULL,
  `end` datetime(6) NOT NULL,
  `xmin` int(11) NOT NULL,
  `xmax` int(11) NOT NULL,
  `ymin` int(11) NOT NULL,
  `ymax` int(11) NOT NULL,
  `numframes` int(11) NOT NULL,
  `locktime` datetime(6) DEFAULT NULL,
  `done` tinyint(1) NOT NULL,
  `videoclip` varchar(256) NOT NULL,
  `double` tinyint(1) NOT NULL,
  `hasarchive` tinyint(1) NOT NULL,
  `school_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `eventers_event_school_id_f65d815f_fk_tf_workers_school_id` (`school_id`),
  CONSTRAINT `eventers_event_school_id_f65d815f_fk_tf_workers_school_id` FOREIGN KEY (`school_id`) REFERENCES `tf_workers_school` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `eventers_event`
--

LOCK TABLES `eventers_event` WRITE;
/*!40000 ALTER TABLE `eventers_event` DISABLE KEYS */;
/*!40000 ALTER TABLE `eventers_event` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `eventers_event_frame`
--

DROP TABLE IF EXISTS `eventers_event_frame`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `eventers_event_frame` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `time` datetime(6) NOT NULL,
  `status` smallint(6) NOT NULL,
  `name` varchar(100) NOT NULL,
  `x1` int(11) NOT NULL,
  `x2` int(11) NOT NULL,
  `y1` int(11) NOT NULL,
  `y2` int(11) NOT NULL,
  `trainframe` bigint(20) NOT NULL,
  `hasarchive` tinyint(1) NOT NULL,
  `event_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `eventers_event_frame_event_id_8ccad010_fk_eventers_event_id` (`event_id`),
  CONSTRAINT `eventers_event_frame_event_id_8ccad010_fk_eventers_event_id` FOREIGN KEY (`event_id`) REFERENCES `eventers_event` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `eventers_event_frame`
--

LOCK TABLES `eventers_event_frame` WRITE;
/*!40000 ALTER TABLE `eventers_event_frame` DISABLE KEYS */;
/*!40000 ALTER TABLE `eventers_event_frame` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `eventers_evt_condition`
--

DROP TABLE IF EXISTS `eventers_evt_condition`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `eventers_evt_condition` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `reaction` int(11) NOT NULL,
  `and_or` int(11) NOT NULL,
  `c_type` int(11) NOT NULL,
  `x` int(11) NOT NULL,
  `y` double NOT NULL,
  `bracket` int(11) NOT NULL,
  `eventer_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `eventers_evt_condition_eventer_id_81d1605a_fk_streams_stream_id` (`eventer_id`),
  CONSTRAINT `eventers_evt_condition_eventer_id_81d1605a_fk_streams_stream_id` FOREIGN KEY (`eventer_id`) REFERENCES `streams_stream` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `eventers_evt_condition`
--

LOCK TABLES `eventers_evt_condition` WRITE;
/*!40000 ALTER TABLE `eventers_evt_condition` DISABLE KEYS */;
/*!40000 ALTER TABLE `eventers_evt_condition` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `schools_tag`
--

DROP TABLE IF EXISTS `schools_tag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `schools_tag` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` varchar(100) NOT NULL,
  `school` smallint(6) NOT NULL,
  `replaces` smallint(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `schools_tag`
--

LOCK TABLES `schools_tag` WRITE;
/*!40000 ALTER TABLE `schools_tag` DISABLE KEYS */;
INSERT INTO `schools_tag` VALUES (1,'night','Night',1,-1),(2,'human','Human(s)',1,-1),(3,'cat','Cat(s)',1,-1),(4,'dog','Dog(s)',1,-1),(5,'bird','Bird(s)',1,-1),(6,'insect','Insect(s)',1,-1),(7,'car','Car(s)',1,-1),(8,'truck','Truck(s)',1,-1),(9,'motorcycle','Motorcycle(s)',1,-1),(10,'bicycle','Bicycle(s)',1,-1);
/*!40000 ALTER TABLE `schools_tag` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `streams_stream`
--

DROP TABLE IF EXISTS `streams_stream`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `streams_stream` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `active` tinyint(1) NOT NULL,
  `name` varchar(100) NOT NULL,
  `made` datetime(6) NOT NULL,
  `lastused` datetime(6) NOT NULL,
  `cam_mode_flag` int(11) NOT NULL,
  `cam_view` tinyint(1) NOT NULL,
  `cam_xres` int(11) NOT NULL,
  `cam_yres` int(11) NOT NULL,
  `cam_fpslimit` double NOT NULL,
  `cam_fpsactual` double NOT NULL,
  `cam_min_x_view` int(11) NOT NULL,
  `cam_max_x_view` int(11) NOT NULL,
  `cam_scale_x_view` double NOT NULL,
  `cam_feed_type` int(11) NOT NULL,
  `cam_url` varchar(256) NOT NULL,
  `cam_apply_mask` tinyint(1) NOT NULL,
  `cam_repeater` int(11) NOT NULL,
  `cam_checkdoubles` tinyint(1) NOT NULL,
  `cam_latency` double NOT NULL,
  `cam_ffmpeg_fps` double NOT NULL,
  `cam_ffmpeg_segment` double NOT NULL,
  `cam_ffmpeg_crf` int(11) NOT NULL,
  `cam_video_codec` int(11) NOT NULL,
  `cam_audio_codec` int(11) NOT NULL,
  `det_mode_flag` int(11) NOT NULL,
  `det_view` tinyint(1) NOT NULL,
  `det_fpslimit` double NOT NULL,
  `det_fpsactual` double NOT NULL,
  `det_min_x_view` int(11) NOT NULL,
  `det_max_x_view` int(11) NOT NULL,
  `det_scale_x_view` double NOT NULL,
  `det_threshold` int(11) NOT NULL,
  `det_backgr_delay` int(11) NOT NULL,
  `det_dilation` int(11) NOT NULL,
  `det_erosion` int(11) NOT NULL,
  `det_max_rect` int(11) NOT NULL,
  `det_max_size` int(11) NOT NULL,
  `det_apply_mask` tinyint(1) NOT NULL,
  `eve_mode_flag` int(11) NOT NULL,
  `eve_view` tinyint(1) NOT NULL,
  `eve_fpslimit` double NOT NULL,
  `eve_fpsactual` double NOT NULL,
  `eve_min_x_view` int(11) NOT NULL,
  `eve_max_x_view` int(11) NOT NULL,
  `eve_scale_x_view` double NOT NULL,
  `eve_alarm_email` varchar(255) NOT NULL,
  `eve_event_time_gap` int(11) NOT NULL,
  `eve_margin` int(11) NOT NULL,
  `eve_all_predictions` tinyint(1) NOT NULL,
  `eve_school_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `streams_stream_eve_school_id_3e307b1b_fk_tf_workers_school_id` (`eve_school_id`),
  CONSTRAINT `streams_stream_eve_school_id_3e307b1b_fk_tf_workers_school_id` FOREIGN KEY (`eve_school_id`) REFERENCES `tf_workers_school` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `streams_stream`
--

LOCK TABLES `streams_stream` WRITE;
/*!40000 ALTER TABLE `streams_stream` DISABLE KEYS */;
/*!40000 ALTER TABLE `streams_stream` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tf_workers_school`
--

DROP TABLE IF EXISTS `tf_workers_school`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tf_workers_school` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `dir` varchar(256) NOT NULL,
  `trigger` int(11) NOT NULL,
  `lastmodelfile` datetime(6) NOT NULL,
  `active` int(11) NOT NULL,
  `l_rate_min` varchar(20) NOT NULL,
  `l_rate_max` varchar(20) NOT NULL,
  `e_school` int(11) NOT NULL,
  `model_type` varchar(50) NOT NULL,
  `ignore_checked` tinyint(1) NOT NULL,
  `extra_runs` int(11) NOT NULL,
  `donate_pics` tinyint(1) NOT NULL,
  `weight_max` double NOT NULL,
  `weight_min` double NOT NULL,
  `weight_boost` double NOT NULL,
  `patience` int(11) NOT NULL,
  `tf_worker_id` bigint(20) NOT NULL,
  `trainer_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tf_workers_school_tf_worker_id_3c7f9633_fk_tf_workers_worker_id` (`tf_worker_id`),
  KEY `tf_workers_school_trainer_id_171876a2_fk_trainers_trainer_id` (`trainer_id`),
  CONSTRAINT `tf_workers_school_tf_worker_id_3c7f9633_fk_tf_workers_worker_id` FOREIGN KEY (`tf_worker_id`) REFERENCES `tf_workers_worker` (`id`),
  CONSTRAINT `tf_workers_school_trainer_id_171876a2_fk_trainers_trainer_id` FOREIGN KEY (`trainer_id`) REFERENCES `trainers_trainer` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tf_workers_school`
--

LOCK TABLES `tf_workers_school` WRITE;
/*!40000 ALTER TABLE `tf_workers_school` DISABLE KEYS */;
/*!40000 ALTER TABLE `tf_workers_school` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tf_workers_worker`
--

DROP TABLE IF EXISTS `tf_workers_worker`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tf_workers_worker` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `active` tinyint(1) NOT NULL,
  `name` varchar(100) NOT NULL,
  `maxblock` int(11) NOT NULL,
  `timeout` double NOT NULL,
  `max_nr_models` int(11) NOT NULL,
  `max_nr_clients` int(11) NOT NULL,
  `gpu_sim_loading` double NOT NULL,
  `gpu_sim` double NOT NULL,
  `gpu_nr` int(11) NOT NULL,
  `savestats` double NOT NULL,
  `use_websocket` tinyint(1) NOT NULL,
  `wsserver` varchar(255) NOT NULL,
  `wsname` varchar(50) NOT NULL,
  `wspass` varchar(50) NOT NULL,
  `wsadminpass` varchar(50) NOT NULL,
  `wsid` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tf_workers_worker`
--

LOCK TABLES `tf_workers_worker` WRITE;
/*!40000 ALTER TABLE `tf_workers_worker` DISABLE KEYS */;
INSERT INTO `tf_workers_worker` VALUES (1,0,'TF-Worker 1',8,0.1,64,20,0,-1,0,0,1,'wss://django.cam-ai.de/','','','',0);
/*!40000 ALTER TABLE `tf_workers_worker` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tools_camurl`
--

DROP TABLE IF EXISTS `tools_camurl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tools_camurl` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `type` varchar(100) NOT NULL,
  `url` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tools_camurl`
--

LOCK TABLES `tools_camurl` WRITE;
/*!40000 ALTER TABLE `tools_camurl` DISABLE KEYS */;
INSERT INTO `tools_camurl` VALUES (1,'Reolink RLC-410W','/bcs/channel0_main.bcs?channel=0&stream=1&user={user}&password={password}');
/*!40000 ALTER TABLE `tools_camurl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tools_setting`
--

DROP TABLE IF EXISTS `tools_setting`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tools_setting` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `setting` varchar(100) NOT NULL,
  `value` varchar(100) NOT NULL,
  `comment` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tools_setting`
--

LOCK TABLES `tools_setting` WRITE;
/*!40000 ALTER TABLE `tools_setting` DISABLE KEYS */;
INSERT INTO `tools_setting` VALUES (1,'loglevel','INFO','No Comment'),(2,'emulatestatic','0','No Comment'),(3,'version','0.7.3','No Comment'),(5,'local_trainer','0','No Comment'),(6,'smtp_account','theo@tester.de','No Comment'),(7,'smtp_password','secret','No Comment'),(8,'smtp_server','smtp.?????.com','No Comment'),(9,'smtp_port','465','No Comment'),(10,'smtp_email','theo@tester.de','No Comment'),(11,'smtp_name','CAM-AI Emailer','No Comment'),(12,'system_number','0','No Comment');
/*!40000 ALTER TABLE `tools_setting` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trainers_epoch`
--

DROP TABLE IF EXISTS `trainers_epoch`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trainers_epoch` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `seconds` double NOT NULL,
  `loss` double NOT NULL,
  `cmetrics` double NOT NULL,
  `hit100` double NOT NULL,
  `val_loss` double NOT NULL,
  `val_cmetrics` double NOT NULL,
  `val_hit100` double NOT NULL,
  `learning_rate` double NOT NULL,
  `fit_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `trainers_epoch_fit_id_5b11bff0_fk_trainers_fit_id` (`fit_id`),
  CONSTRAINT `trainers_epoch_fit_id_5b11bff0_fk_trainers_fit_id` FOREIGN KEY (`fit_id`) REFERENCES `trainers_fit` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trainers_epoch`
--

LOCK TABLES `trainers_epoch` WRITE;
/*!40000 ALTER TABLE `trainers_epoch` DISABLE KEYS */;
/*!40000 ALTER TABLE `trainers_epoch` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trainers_fit`
--

DROP TABLE IF EXISTS `trainers_fit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trainers_fit` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `made` datetime(6) NOT NULL,
  `minutes` double NOT NULL,
  `school` int(11) NOT NULL,
  `epochs` int(11) NOT NULL,
  `nr_tr` int(11) NOT NULL,
  `nr_va` int(11) NOT NULL,
  `loss` double NOT NULL,
  `cmetrics` double NOT NULL,
  `hit100` double NOT NULL,
  `val_loss` double NOT NULL,
  `val_cmetrics` double NOT NULL,
  `val_hit100` double NOT NULL,
  `cputemp` double NOT NULL,
  `cpufan1` double NOT NULL,
  `cpufan2` double NOT NULL,
  `gputemp` double NOT NULL,
  `gpufan` double NOT NULL,
  `description` longtext NOT NULL,
  `status` varchar(10) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trainers_fit`
--

LOCK TABLES `trainers_fit` WRITE;
/*!40000 ALTER TABLE `trainers_fit` DISABLE KEYS */;
/*!40000 ALTER TABLE `trainers_fit` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trainers_trainer`
--

DROP TABLE IF EXISTS `trainers_trainer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trainers_trainer` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `active` tinyint(1) NOT NULL,
  `name` varchar(256) NOT NULL,
  `t_type` int(11) NOT NULL,
  `gpu_nr` int(11) NOT NULL,
  `gpu_mem_limit` int(11) NOT NULL,
  `startworking` varchar(8) NOT NULL,
  `stopworking` varchar(8) NOT NULL,
  `running` tinyint(1) NOT NULL,
  `wsserver` varchar(255) NOT NULL,
  `wsname` varchar(50) NOT NULL,
  `wspass` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trainers_trainer`
--

LOCK TABLES `trainers_trainer` WRITE;
/*!40000 ALTER TABLE `trainers_trainer` DISABLE KEYS */;
INSERT INTO `trainers_trainer` VALUES (1,1,'Trainer 1',3,0,0,'00:00:00','24:00:00',1,'wss://django.cam-ai.de/','','');
/*!40000 ALTER TABLE `trainers_trainer` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trainers_trainframe`
--

DROP TABLE IF EXISTS `trainers_trainframe`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trainers_trainframe` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `made` datetime(6) NOT NULL,
  `school` smallint(6) NOT NULL,
  `name` varchar(256) NOT NULL,
  `code` varchar(2) NOT NULL,
  `c0` smallint(6) NOT NULL,
  `c1` smallint(6) NOT NULL,
  `c2` smallint(6) NOT NULL,
  `c3` smallint(6) NOT NULL,
  `c4` smallint(6) NOT NULL,
  `c5` smallint(6) NOT NULL,
  `c6` smallint(6) NOT NULL,
  `c7` smallint(6) NOT NULL,
  `c8` smallint(6) NOT NULL,
  `c9` smallint(6) NOT NULL,
  `checked` smallint(6) NOT NULL,
  `train_status` smallint(6) NOT NULL,
  `made_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `trainers_trainframe_made_by_id_4562a1cb_fk_auth_user_id` (`made_by_id`),
  CONSTRAINT `trainers_trainframe_made_by_id_4562a1cb_fk_auth_user_id` FOREIGN KEY (`made_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=316 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trainers_trainframe`
--

LOCK TABLES `trainers_trainframe` WRITE;
/*!40000 ALTER TABLE `trainers_trainframe` DISABLE KEYS */;
INSERT INTO `trainers_trainframe` VALUES (217,'2022-11-23 14:54:08.261776',2,'frames/2_54_2022-11-23-14-54-08-261776.bmp','NE',0,1,0,0,0,0,0,0,0,0,0,0,1),(218,'2022-11-23 14:54:08.757400',2,'frames/2_86_2022-11-23-14-54-08-757400.bmp','NE',0,1,0,0,0,0,0,0,0,0,0,0,1),(219,'2022-11-23 14:54:09.238146',2,'frames/2_45_2022-11-23-14-54-09-238146.bmp','NE',0,1,0,0,0,0,0,0,0,0,0,0,1),(220,'2022-11-25 18:54:51.156105',1,'frames/1_29_2022-11-25-18-54-51-156105.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(221,'2022-11-25 18:54:53.414803',1,'frames/1_15_2022-11-25-18-54-53-414803.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(222,'2022-11-25 18:54:53.918315',1,'frames/1_57_2022-11-25-18-54-53-918315.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(223,'2022-11-25 18:54:54.425560',1,'frames/1_78_2022-11-25-18-54-54-425560.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(224,'2022-11-25 18:54:55.268285',1,'frames/1_3_2022-11-25-18-54-55-268285.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(225,'2022-11-25 18:54:55.443794',1,'frames/1_21_2022-11-25-18-54-55-443794.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(226,'2022-11-25 18:54:55.947945',1,'frames/1_44_2022-11-25-18-54-55-947945.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(227,'2022-11-25 18:54:56.433488',1,'frames/1_2_2022-11-25-18-54-56-433488.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(228,'2022-11-25 18:54:57.319085',1,'frames/1_87_2022-11-25-18-54-57-319085.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(229,'2022-11-25 18:54:57.463925',1,'frames/1_3_2022-11-25-18-54-57-463925.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(230,'2022-11-25 18:54:57.903229',1,'frames/1_13_2022-11-25-18-54-57-903229.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(231,'2022-11-25 18:54:58.418328',1,'frames/1_23_2022-11-25-18-54-58-418328.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(232,'2022-11-25 18:54:59.181974',1,'frames/1_91_2022-11-25-18-54-59-181974.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(233,'2022-11-25 18:54:59.424638',1,'frames/1_74_2022-11-25-18-54-59-424638.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(234,'2022-11-25 18:54:59.911529',1,'frames/1_41_2022-11-25-18-54-59-911529.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(235,'2022-11-25 18:55:00.407157',1,'frames/1_68_2022-11-25-18-55-00-407157.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(236,'2022-11-25 18:55:01.215931',1,'frames/1_15_2022-11-25-18-55-01-215931.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(237,'2022-11-25 18:55:01.435166',1,'frames/1_8_2022-11-25-18-55-01-435166.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(238,'2022-11-25 18:55:01.915035',1,'frames/1_66_2022-11-25-18-55-01-915035.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(239,'2022-11-25 18:55:02.404831',1,'frames/1_75_2022-11-25-18-55-02-404831.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(240,'2022-11-25 18:55:03.185070',1,'frames/1_49_2022-11-25-18-55-03-185070.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(241,'2022-11-25 18:55:03.429109',1,'frames/1_98_2022-11-25-18-55-03-429109.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(242,'2022-11-25 18:55:03.923038',1,'frames/1_37_2022-11-25-18-55-03-923038.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(243,'2022-11-25 18:55:04.411971',1,'frames/1_55_2022-11-25-18-55-04-411971.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(244,'2022-11-25 18:55:05.155168',1,'frames/1_26_2022-11-25-18-55-05-155168.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(245,'2022-11-25 18:55:05.436262',1,'frames/1_18_2022-11-25-18-55-05-436262.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(246,'2022-11-25 18:55:05.910045',1,'frames/1_53_2022-11-25-18-55-05-910045.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(247,'2022-11-25 18:55:06.399087',1,'frames/1_98_2022-11-25-18-55-06-399087.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(248,'2022-11-25 18:55:07.254724',1,'frames/1_53_2022-11-25-18-55-07-254724.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(249,'2022-11-25 18:55:07.501983',1,'frames/1_56_2022-11-25-18-55-07-501983.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(250,'2022-11-25 18:55:07.928572',1,'frames/1_51_2022-11-25-18-55-07-928572.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(251,'2022-11-25 18:55:08.423126',1,'frames/1_99_2022-11-25-18-55-08-423126.bmp','NE',0,0,0,0,0,0,0,0,0,0,1,2,1),(252,'2022-11-25 18:55:12.422385',1,'frames/1_45_2022-11-25-18-55-12-422385.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(253,'2022-11-25 18:55:13.119250',1,'frames/1_18_2022-11-25-18-55-13-119250.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(254,'2022-11-25 18:55:14.419286',1,'frames/1_47_2022-11-25-18-55-14-419286.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(255,'2022-11-25 18:55:19.879766',1,'frames/1_71_2022-11-25-18-55-19-879766.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(256,'2022-11-25 18:55:20.438469',1,'frames/1_88_2022-11-25-18-55-20-438469.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(257,'2022-11-25 18:55:21.190580',1,'frames/1_48_2022-11-25-18-55-21-190580.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(258,'2022-11-25 18:55:21.440033',1,'frames/1_62_2022-11-25-18-55-21-440033.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(259,'2022-11-25 18:55:25.924601',1,'frames/1_21_2022-11-25-18-55-25-924601.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(260,'2022-11-25 18:55:26.402965',1,'frames/1_18_2022-11-25-18-55-26-402965.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(261,'2022-11-25 18:56:12.435043',1,'frames/1_66_2022-11-25-18-56-12-435043.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(262,'2022-11-25 18:56:14.421986',1,'frames/1_46_2022-11-25-18-56-14-421986.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(263,'2022-11-25 18:56:15.173031',1,'frames/1_58_2022-11-25-18-56-15-173031.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(264,'2022-11-25 18:56:15.392700',1,'frames/1_87_2022-11-25-18-56-15-392700.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(265,'2022-11-25 18:56:15.941073',1,'frames/1_21_2022-11-25-18-56-15-941073.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(266,'2022-11-25 18:56:16.408817',1,'frames/1_38_2022-11-25-18-56-16-408817.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(267,'2022-11-25 18:56:17.269796',1,'frames/1_13_2022-11-25-18-56-17-269796.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(268,'2022-11-25 18:56:17.521926',1,'frames/1_45_2022-11-25-18-56-17-521926.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(269,'2022-11-25 18:56:17.917698',1,'frames/1_26_2022-11-25-18-56-17-917698.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(270,'2022-11-25 18:56:18.406397',1,'frames/1_95_2022-11-25-18-56-18-406397.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(271,'2022-11-25 18:56:19.212513',1,'frames/1_88_2022-11-25-18-56-19-212513.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(272,'2022-11-25 18:56:19.442277',1,'frames/1_95_2022-11-25-18-56-19-442277.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(273,'2022-11-25 18:56:19.907201',1,'frames/1_57_2022-11-25-18-56-19-907201.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(274,'2022-11-25 18:56:20.417075',1,'frames/1_66_2022-11-25-18-56-20-417075.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(275,'2022-11-25 18:56:21.903021',1,'frames/1_90_2022-11-25-18-56-21-903021.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(276,'2022-11-25 18:56:22.408722',1,'frames/1_20_2022-11-25-18-56-22-408722.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(277,'2022-11-25 18:56:23.212898',1,'frames/1_27_2022-11-25-18-56-23-212898.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(278,'2022-11-25 18:56:56.399954',1,'frames/1_24_2022-11-25-18-56-56-399954.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(279,'2022-11-25 18:56:59.186587',1,'frames/1_34_2022-11-25-18-56-59-186587.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(280,'2022-11-25 18:57:00.399538',1,'frames/1_32_2022-11-25-18-57-00-399538.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(281,'2022-11-25 18:57:01.141694',1,'frames/1_52_2022-11-25-18-57-01-141694.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(282,'2022-11-25 18:57:01.422594',1,'frames/1_53_2022-11-25-18-57-01-422594.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(283,'2022-11-25 18:57:47.417989',1,'frames/1_27_2022-11-25-18-57-47-417989.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(284,'2022-11-25 18:54:51.156114',1,'frames/1_61_2022-11-25-18-54-51-156114.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(285,'2022-11-25 18:54:51.417349',1,'frames/1_70_2022-11-25-18-54-51-417349.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(286,'2022-11-25 18:54:51.914625',1,'frames/1_91_2022-11-25-18-54-51-914625.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(287,'2022-11-25 18:54:52.413651',1,'frames/1_64_2022-11-25-18-54-52-413651.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(288,'2022-11-25 18:54:53.414810',1,'frames/1_0_2022-11-25-18-54-53-414810.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(289,'2022-11-25 18:54:54.425566',1,'frames/1_71_2022-11-25-18-54-54-425566.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(290,'2022-11-25 18:54:55.268290',1,'frames/1_5_2022-11-25-18-54-55-268290.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(291,'2022-11-25 18:54:58.418332',1,'frames/1_67_2022-11-25-18-54-58-418332.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(292,'2022-11-25 18:55:05.155172',1,'frames/1_76_2022-11-25-18-55-05-155172.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(293,'2022-11-25 18:55:06.399092',1,'frames/1_4_2022-11-25-18-55-06-399092.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(294,'2022-11-25 18:55:20.438476',1,'frames/1_85_2022-11-25-18-55-20-438476.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(295,'2022-11-25 18:55:21.190587',1,'frames/1_42_2022-11-25-18-55-21-190587.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(296,'2022-11-25 18:55:21.440041',1,'frames/1_95_2022-11-25-18-55-21-440041.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(297,'2022-11-25 18:55:21.972075',1,'frames/1_64_2022-11-25-18-55-21-972075.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(298,'2022-11-25 18:55:57.502802',1,'frames/1_72_2022-11-25-18-55-57-502802.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(299,'2022-11-25 18:55:57.921779',1,'frames/1_61_2022-11-25-18-55-57-921779.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(300,'2022-11-25 18:55:58.426617',1,'frames/1_52_2022-11-25-18-55-58-426617.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(301,'2022-11-25 18:55:59.411919',1,'frames/1_55_2022-11-25-18-55-59-411919.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(302,'2022-11-25 18:56:02.401589',1,'frames/1_72_2022-11-25-18-56-02-401589.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(303,'2022-11-25 18:56:05.909186',1,'frames/1_18_2022-11-25-18-56-05-909186.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(304,'2022-11-25 18:56:07.281091',1,'frames/1_86_2022-11-25-18-56-07-281091.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(305,'2022-11-25 18:56:07.522200',1,'frames/1_14_2022-11-25-18-56-07-522200.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(306,'2022-11-25 18:56:07.897511',1,'frames/1_33_2022-11-25-18-56-07-897511.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(307,'2022-11-25 18:56:22.408726',1,'frames/1_77_2022-11-25-18-56-22-408726.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(308,'2022-11-25 18:56:23.212902',1,'frames/1_66_2022-11-25-18-56-23-212902.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(309,'2022-11-25 18:56:56.399957',1,'frames/1_45_2022-11-25-18-56-56-399957.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(310,'2022-11-25 18:57:00.399541',1,'frames/1_39_2022-11-25-18-57-00-399541.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(311,'2022-11-25 18:57:02.405108',1,'frames/1_91_2022-11-25-18-57-02-405108.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(312,'2022-11-25 18:57:04.402814',1,'frames/1_13_2022-11-25-18-57-04-402814.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(313,'2022-11-25 18:57:05.191435',1,'frames/1_70_2022-11-25-18-57-05-191435.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(314,'2022-11-25 18:57:05.441719',1,'frames/1_88_2022-11-25-18-57-05-441719.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1),(315,'2022-11-25 18:57:05.933418',1,'frames/1_90_2022-11-25-18-57-05-933418.bmp','NE',0,1,0,0,0,0,0,0,0,0,1,2,1);
/*!40000 ALTER TABLE `trainers_trainframe` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_archive`
--

DROP TABLE IF EXISTS `users_archive`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_archive` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `typecode` int(11) NOT NULL,
  `number` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `made` datetime(6) NOT NULL,
  `school_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `users_archive_school_id_75692b37_fk_tf_workers_school_id` (`school_id`),
  CONSTRAINT `users_archive_school_id_75692b37_fk_tf_workers_school_id` FOREIGN KEY (`school_id`) REFERENCES `tf_workers_school` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_archive`
--

LOCK TABLES `users_archive` WRITE;
/*!40000 ALTER TABLE `users_archive` DISABLE KEYS */;
/*!40000 ALTER TABLE `users_archive` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_archive_users`
--

DROP TABLE IF EXISTS `users_archive_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_archive_users` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `archive_id` bigint(20) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `users_archive_users_archive_id_user_id_d53f1dec_uniq` (`archive_id`,`user_id`),
  KEY `users_archive_users_user_id_84bbf87a_fk_auth_user_id` (`user_id`),
  CONSTRAINT `users_archive_users_archive_id_4eb6a3aa_fk_users_archive_id` FOREIGN KEY (`archive_id`) REFERENCES `users_archive` (`id`),
  CONSTRAINT `users_archive_users_user_id_84bbf87a_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_archive_users`
--

LOCK TABLES `users_archive_users` WRITE;
/*!40000 ALTER TABLE `users_archive_users` DISABLE KEYS */;
/*!40000 ALTER TABLE `users_archive_users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_userinfo`
--

DROP TABLE IF EXISTS `users_userinfo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_userinfo` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `client_nr_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `users_userinfo_user_id_6acffaf6_fk_auth_user_id` (`user_id`),
  KEY `users_userinfo_client_nr_id_6a9f9eae_fk_ws_predictions_client_id` (`client_nr_id`),
  CONSTRAINT `users_userinfo_client_nr_id_6a9f9eae_fk_ws_predictions_client_id` FOREIGN KEY (`client_nr_id`) REFERENCES `ws_predictions_client` (`id`),
  CONSTRAINT `users_userinfo_user_id_6acffaf6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_userinfo`
--

LOCK TABLES `users_userinfo` WRITE;
/*!40000 ALTER TABLE `users_userinfo` DISABLE KEYS */;
INSERT INTO `users_userinfo` VALUES (1,1,NULL);
/*!40000 ALTER TABLE `users_userinfo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `viewers_view_log`
--

DROP TABLE IF EXISTS `viewers_view_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `viewers_view_log` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `v_type` varchar(1) NOT NULL,
  `v_id` int(11) NOT NULL,
  `start` datetime(6) NOT NULL,
  `stop` datetime(6) NOT NULL,
  `user` int(11) NOT NULL,
  `active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `viewers_view_log`
--

LOCK TABLES `viewers_view_log` WRITE;
/*!40000 ALTER TABLE `viewers_view_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `viewers_view_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ws_predictions_client`
--

DROP TABLE IF EXISTS `ws_predictions_client`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ws_predictions_client` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `hash` varchar(100) NOT NULL,
  `comment` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ws_predictions_client`
--

LOCK TABLES `ws_predictions_client` WRITE;
/*!40000 ALTER TABLE `ws_predictions_client` DISABLE KEYS */;
/*!40000 ALTER TABLE `ws_predictions_client` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'CAM-AI_LAST'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2022-12-14 14:49:24
