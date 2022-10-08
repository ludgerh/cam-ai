-- MySQL dump 10.19  Distrib 10.3.34-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: CAM-AI_NEW
-- ------------------------------------------------------
-- Server version	10.3.34-MariaDB-0+deb10u1

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
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `access_access_control`
--

LOCK TABLES `access_access_control` WRITE;
/*!40000 ALTER TABLE `access_access_control` DISABLE KEYS */;
INSERT INTO `access_access_control` VALUES (1,'X',1,'U',0,'W'),(2,'S',1,'U',0,'W');
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
) ENGINE=InnoDB AUTO_INCREMENT=121 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add eventer',7,'add_eventer'),(26,'Can change eventer',7,'change_eventer'),(27,'Can delete eventer',7,'delete_eventer'),(28,'Can view eventer',7,'view_eventer'),(29,'Can add detector',8,'add_detector'),(30,'Can change detector',8,'change_detector'),(31,'Can delete detector',8,'delete_detector'),(32,'Can view detector',8,'view_detector'),(33,'Can add stream',9,'add_stream'),(34,'Can change stream',9,'change_stream'),(35,'Can delete stream',9,'delete_stream'),(36,'Can view stream',9,'view_stream'),(37,'Can add cam',10,'add_cam'),(38,'Can change cam',10,'change_cam'),(39,'Can delete cam',10,'delete_cam'),(40,'Can view cam',10,'view_cam'),(41,'Can add setting',11,'add_setting'),(42,'Can change setting',11,'change_setting'),(43,'Can delete setting',11,'delete_setting'),(44,'Can view setting',11,'view_setting'),(45,'Can add viewer',12,'add_viewer'),(46,'Can change viewer',12,'change_viewer'),(47,'Can delete viewer',12,'delete_viewer'),(48,'Can view viewer',12,'view_viewer'),(49,'Can add access_control',13,'add_access_control'),(50,'Can change access_control',13,'change_access_control'),(51,'Can delete access_control',13,'delete_access_control'),(52,'Can view access_control',13,'view_access_control'),(53,'Can add view_log',14,'add_view_log'),(54,'Can change view_log',14,'change_view_log'),(55,'Can delete view_log',14,'delete_view_log'),(56,'Can view view_log',14,'view_view_log'),(57,'Can add worker',15,'add_worker'),(58,'Can change worker',15,'change_worker'),(59,'Can delete worker',15,'delete_worker'),(60,'Can view worker',15,'view_worker'),(61,'Can add school',16,'add_school'),(62,'Can change school',16,'change_school'),(63,'Can delete school',16,'delete_school'),(64,'Can view school',16,'view_school'),(65,'Can add tag',17,'add_tag'),(66,'Can change tag',17,'change_tag'),(67,'Can delete tag',17,'delete_tag'),(68,'Can view tag',17,'view_tag'),(69,'Can add event_frame',18,'add_event_frame'),(70,'Can change event_frame',18,'change_event_frame'),(71,'Can delete event_frame',18,'delete_event_frame'),(72,'Can view event_frame',18,'view_event_frame'),(73,'Can add event',19,'add_event'),(74,'Can change event',19,'change_event'),(75,'Can delete event',19,'delete_event'),(76,'Can view event',19,'view_event'),(77,'Can add mask',20,'add_mask'),(78,'Can change mask',20,'change_mask'),(79,'Can delete mask',20,'delete_mask'),(80,'Can view mask',20,'view_mask'),(81,'Can add tag',21,'add_tag'),(82,'Can change tag',21,'change_tag'),(83,'Can delete tag',21,'delete_tag'),(84,'Can view tag',21,'view_tag'),(85,'Can add evt_condition',22,'add_evt_condition'),(86,'Can change evt_condition',22,'change_evt_condition'),(87,'Can delete evt_condition',22,'delete_evt_condition'),(88,'Can view evt_condition',22,'view_evt_condition'),(89,'Can add userinfo',23,'add_userinfo'),(90,'Can change userinfo',23,'change_userinfo'),(91,'Can delete userinfo',23,'delete_userinfo'),(92,'Can view userinfo',23,'view_userinfo'),(93,'Can add trainframe',24,'add_trainframe'),(94,'Can change trainframe',24,'change_trainframe'),(95,'Can delete trainframe',24,'delete_trainframe'),(96,'Can view trainframe',24,'view_trainframe'),(97,'Can add trainframe',25,'add_trainframe'),(98,'Can change trainframe',25,'change_trainframe'),(99,'Can delete trainframe',25,'delete_trainframe'),(100,'Can view trainframe',25,'view_trainframe'),(101,'Can add trainer',26,'add_trainer'),(102,'Can change trainer',26,'change_trainer'),(103,'Can delete trainer',26,'delete_trainer'),(104,'Can view trainer',26,'view_trainer'),(105,'Can add archive',27,'add_archive'),(106,'Can change archive',27,'change_archive'),(107,'Can delete archive',27,'delete_archive'),(108,'Can view archive',27,'view_archive'),(109,'Can add epoch',28,'add_epoch'),(110,'Can change epoch',28,'change_epoch'),(111,'Can delete epoch',28,'delete_epoch'),(112,'Can view epoch',28,'view_epoch'),(113,'Can add fit',29,'add_fit'),(114,'Can change fit',29,'change_fit'),(115,'Can delete fit',29,'delete_fit'),(116,'Can view fit',29,'view_fit'),(117,'Can add view_log',30,'add_view_log'),(118,'Can change view_log',30,'change_view_log'),(119,'Can delete view_log',30,'delete_view_log'),(120,'Can view view_log',30,'view_view_log');
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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$320000$DSkczyhVTs6EcMVMNkM00G$w36zQFEJ0AmDCsOhOtuKDzM3gotKGT957w3BfNVk1GY=','2022-09-18 10:26:51.367997',1,'ludger','Ludger','Hellerhoff','ludger@booker-hellerhoff.de',1,1,'2022-01-23 19:32:53.722067'),(2,'pbkdf2_sha256$320000$mDdZuLurHN68DbR93QLKy6$HE0Kc0qxaKizdIPK0FsRSY8ATMGSnENn9MqDRyhkx2o=','2022-07-17 14:16:10.049419',0,'theo','Theo','Tester','theo@tester.de',0,1,'2022-01-23 20:26:07.345845');
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
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2022-07-17 14:05:36.891657','2','S_0 U_0 W',2,'[]',13,1),(2,'2022-07-17 14:09:24.280438','2','S_0 U_0 W',2,'[]',13,1),(3,'2022-07-17 14:14:39.290357','2','S_1 U_0 W',2,'[{\"changed\": {\"fields\": [\"Vid\"]}}]',13,1),(4,'2022-07-17 14:14:55.220654','1','X_1 U_0 W',2,'[{\"changed\": {\"fields\": [\"Vid\"]}}]',13,1),(5,'2022-07-17 14:15:24.399333','5','X_2 U_0 R',1,'[{\"added\": {}}]',13,1),(6,'2022-07-17 14:15:39.730304','6','S_2 U_0 R',1,'[{\"added\": {}}]',13,1),(7,'2022-07-18 11:23:48.969661','6','S_2 U_0 W',2,'[{\"changed\": {\"fields\": [\"R w\"]}}]',13,1),(8,'2022-07-18 11:24:05.572465','5','X_2 U_0 W',2,'[{\"changed\": {\"fields\": [\"R w\"]}}]',13,1);
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
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (13,'access','access_control'),(1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(5,'contenttypes','contenttype'),(20,'drawpad','mask'),(19,'eventers','event'),(18,'eventers','event_frame'),(22,'eventers','evt_condition'),(14,'index','view_log'),(21,'schools','tag'),(6,'sessions','session'),(10,'streams','cam'),(8,'streams','detector'),(7,'streams','eventer'),(9,'streams','stream'),(16,'tf_workers','school'),(17,'tf_workers','tag'),(15,'tf_workers','worker'),(11,'tools','setting'),(24,'trainer','trainframe'),(28,'trainers','epoch'),(29,'trainers','fit'),(26,'trainers','trainer'),(25,'trainers','trainframe'),(27,'users','archive'),(23,'users','userinfo'),(12,'viewers','viewer'),(30,'viewers','view_log');
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
) ENGINE=InnoDB AUTO_INCREMENT=97 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2022-01-20 10:48:27.232749'),(2,'auth','0001_initial','2022-01-20 10:48:27.523757'),(3,'admin','0001_initial','2022-01-20 10:48:27.605247'),(4,'admin','0002_logentry_remove_auto_add','2022-01-20 10:48:27.634487'),(5,'admin','0003_logentry_add_action_flag_choices','2022-01-20 10:48:27.647230'),(6,'contenttypes','0002_remove_content_type_name','2022-01-20 10:48:27.696775'),(7,'auth','0002_alter_permission_name_max_length','2022-01-20 10:48:27.731394'),(8,'auth','0003_alter_user_email_max_length','2022-01-20 10:48:27.745771'),(9,'auth','0004_alter_user_username_opts','2022-01-20 10:48:27.756487'),(10,'auth','0005_alter_user_last_login_null','2022-01-20 10:48:27.787980'),(11,'auth','0006_require_contenttypes_0002','2022-01-20 10:48:27.791083'),(12,'auth','0007_alter_validators_add_error_messages','2022-01-20 10:48:27.799358'),(13,'auth','0008_alter_user_username_max_length','2022-01-20 10:48:27.832582'),(14,'auth','0009_alter_user_last_name_max_length','2022-01-20 10:48:27.866532'),(15,'auth','0010_alter_group_name_max_length','2022-01-20 10:48:27.876553'),(16,'auth','0011_update_proxy_permissions','2022-01-20 10:48:27.886793'),(17,'auth','0012_alter_user_first_name_max_length','2022-01-20 10:48:27.922957'),(18,'sessions','0001_initial','2022-01-20 10:48:27.948167'),(19,'streams','0001_initial','2022-01-20 11:21:45.057969'),(20,'tools','0001_initial','2022-01-20 11:21:45.071400'),(21,'viewers','0001_initial','2022-01-21 11:55:44.859589'),(22,'streams','0002_cam_viewer','2022-01-21 14:28:22.579478'),(23,'streams','0003_detector_viewer_eventer_viewer','2022-01-21 14:30:12.120019'),(24,'access','0001_initial','2022-01-21 22:49:35.303828'),(25,'streams','0004_remove_cam_active_remove_detector_active_and_more','2022-01-24 19:53:17.404584'),(26,'index','0001_initial','2022-01-24 21:19:46.764106'),(27,'streams','0005_remove_detector_viewer_remove_eventer_viewer_and_more','2022-01-25 09:04:54.249017'),(28,'streams','0006_stream_det_mode_flag_stream_eve_mode_flag','2022-01-25 09:09:12.604123'),(29,'streams','0007_alter_stream_cam_mode_flag','2022-01-25 18:03:34.639743'),(30,'streams','0008_stream_cam_view_stream_det_view_stream_eve_view','2022-01-26 13:44:12.872851'),(31,'tf_workers','0001_initial','2022-02-06 23:06:36.087590'),(32,'streams','0009_stream_eve_tf_worker','2022-02-06 23:15:50.043184'),(33,'streams','0010_alter_stream_eve_tf_worker','2022-02-06 23:21:12.699578'),(34,'tf_workers','0002_worker_max_nr_models_worker_timeout_worker_wsname','2022-02-11 16:40:54.812842'),(35,'tf_workers','0003_worker_max_nr_clients','2022-02-12 13:20:14.039745'),(36,'tf_workers','0004_school','2022-02-12 20:53:13.713893'),(37,'tf_workers','0005_tag','2022-02-13 11:06:37.585670'),(38,'eventers','0001_initial','2022-02-13 11:08:19.146070'),(39,'streams','0011_stream_eve_all_predictions','2022-02-13 15:28:45.662603'),(40,'drawpad','0001_initial','2022-02-19 21:19:50.687193'),(41,'streams','0012_stream_det_apply_mask','2022-02-20 09:49:59.696380'),(42,'drawpad','0002_rename_cam_mask_stream_mask_mtype','2022-02-20 18:36:03.803522'),(43,'streams','0013_alter_stream_det_fpslimit','2022-02-20 18:36:03.810399'),(44,'schools','0001_initial','2022-02-21 17:28:01.697943'),(45,'streams','0014_alter_stream_eve_fpslimit','2022-02-21 17:28:01.706763'),(46,'eventers','0002_evt_condition','2022-02-22 08:10:50.754897'),(47,'users','0001_initial','2022-02-26 16:10:33.876485'),(48,'streams','0015_remove_stream_eve_tf_worker','2022-02-26 17:21:24.835630'),(49,'tf_workers','0006_school_tf_worker','2022-02-26 17:21:24.885445'),(50,'trainer','0001_initial','2022-02-26 20:56:01.514921'),(51,'trainers','0001_initial','2022-02-28 10:26:36.185638'),(52,'trainers','0002_trainer','2022-02-28 14:40:46.930796'),(53,'trainers','0003_trainer_active','2022-02-28 14:55:07.285045'),(54,'trainers','0004_trainer_last_school_trainer_startworking_and_more','2022-02-28 16:16:08.571481'),(55,'streams','0002_remove_stream_cam_checkdoubles','2022-03-06 16:07:30.333529'),(56,'streams','0003_stream_cam_checkdoubles','2022-03-06 16:08:06.102603'),(57,'eventers','0002_event_archivname_event_frame_archivname','2022-03-16 20:40:45.376279'),(58,'users','0002_archive','2022-03-16 20:40:45.501914'),(59,'users','0003_archive_number','2022-03-17 17:34:30.723559'),(60,'users','0004_rename_user_archive_users','2022-03-18 12:15:25.882445'),(61,'eventers','0003_remove_event_archivname_and_more','2022-03-18 16:52:11.202261'),(62,'tf_workers','0002_alter_school_dir','2022-04-02 19:15:53.583268'),(63,'tf_workers','0003_delete_tag','2022-06-24 20:26:14.926851'),(64,'trainers','0002_fit_epoch','2022-06-27 21:44:11.693116'),(65,'trainers','0003_remove_trainer_device_nr_remove_trainer_last_school_and_more','2022-06-30 11:06:34.868739'),(66,'tf_workers','0004_remove_school_last_id_mf','2022-06-30 11:08:43.560148'),(67,'tf_workers','0005_remove_school_do_filter_remove_school_load_model_nr_and_more','2022-06-30 11:15:19.016605'),(68,'tf_workers','0006_remove_school_lastfile','2022-06-30 11:29:40.967680'),(69,'tf_workers','0003_remove_school_do_filter_remove_school_last_id_mf_and_more','2022-06-30 13:20:17.773505'),(70,'tf_workers','0004_remove_school_last_id_of','2022-06-30 13:32:03.077660'),(71,'tf_workers','0002_delete_tag_alter_school_dir','2022-06-30 13:54:24.479924'),(72,'tf_workers','0004_remove_school_size','2022-06-30 19:55:19.392079'),(73,'tf_workers','0005_school_use_checked','2022-07-01 11:03:14.183299'),(74,'tf_workers','0006_rename_use_checked_school_ignore_checked','2022-07-01 12:01:00.211671'),(75,'tf_workers','0007_alter_school_ignore_checked','2022-07-01 12:01:24.242726'),(76,'trainers','0004_fit_status','2022-07-02 13:15:08.087902'),(77,'trainers','0005_epoch_seconds','2022-07-02 14:08:38.052098'),(78,'tf_workers','0008_remove_school_last_image_id','2022-07-09 11:56:29.511364'),(79,'trainers','0006_trainframe_train_status','2022-07-09 11:56:29.531588'),(80,'streams','0004_stream_cam_latency','2022-07-12 09:39:00.100282'),(81,'tf_workers','0009_school_donate_pics_school_extra_runs','2022-07-12 14:34:38.121044'),(82,'tf_workers','0010_school_trainer','2022-07-13 12:11:21.941628'),(83,'eventers','0004_remove_event_userlock','2022-07-17 17:35:00.367495'),(84,'trainers','0007_epoch_learning_rate_alter_epoch_cmetrics_and_more','2022-07-18 20:36:27.236486'),(85,'streams','0005_stream_cam_audio_codec_stream_cam_ffmpeg_fps_and_more','2022-08-26 13:22:27.306431'),(86,'streams','0006_stream_cam_ffmpeg_segment','2022-08-27 11:51:40.661926'),(87,'streams','0007_stream_cam_ffmpeg_crf_alter_stream_cam_ffmpeg_fps_and_more','2022-08-27 13:03:02.117485'),(88,'viewers','0002_view_log','2022-08-31 14:58:11.114674'),(89,'index','0002_delete_view_log','2022-09-04 17:50:55.293715'),(90,'trainers','0008_trainer_wsname_trainer_wspass_trainer_wsurl_and_more','2022-09-04 17:50:55.319912'),(91,'trainers','0009_remove_trainer_wsname_remove_trainer_wspass','2022-09-05 10:57:35.440029'),(92,'tf_workers','0011_rename_wsurl_worker_wsserver','2022-09-06 13:27:53.684701'),(93,'trainers','0010_rename_wsurl_trainer_wsserver','2022-09-06 13:28:08.136430'),(94,'trainers','0011_trainer_gpu_mem_limit','2022-09-17 16:15:56.699544'),(95,'tf_workers','0012_school_weight_boost_school_weight_max_and_more','2022-09-18 20:28:44.757634'),(96,'tf_workers','0013_school_patience','2022-09-19 10:25:46.084784');
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
INSERT INTO `django_session` VALUES ('1ewrbqrzuw7jekp4u3v8v7nc21b2ic5m','.eJxVjDEOwjAMRe-SGUUureKakZ0zRHZsSAE1UtNOFXenlTrA-t97f3WRlznHpdoUB3UX17jT7yacXjbuQJ88PopPZZynQfyu-INWfytq7-vh_h1krnmrEVIACibduUcEokC9WWJsUQVa6O4NKqgJSctESorWbSayijGD-3wB0VY4Hg:1nBxZ9:Pb8f3e4VUerjp4_zLqpXfayjhsMzPJwAbLakBsoddgc','2022-02-07 11:31:19.528590'),('1whvp9ebi17x16g4dl3zmuks8zojb4xx','.eJxVjDEOwjAMRe-SGUUureKakZ0zRHZsSAE1UtNOFXenlTrA-t97f3WRlznHpdoUB3UX17jT7yacXjbuQJ88PopPZZynQfyu-INWfytq7-vh_h1krnmrEVIACibduUcEokC9WWJsUQVa6O4NKqgJSctESorWbSayijGD-3wB0VY4Hg:1npR3z:J55I5ltK01wa-UkFTpjNFseIRkLCLghLJMQAkdIFq2k','2022-05-27 08:54:19.860649'),('32r44ydpvh4a9162bqkho1n4gbtrvbcq','.eJxVjDEOwjAMRe-SGUUureKakZ0zRHZsSAE1UtNOFXenlTrA-t97f3WRlznHpdoUB3UX17jT7yacXjbuQJ88PopPZZynQfyu-INWfytq7-vh_h1krnmrEVIACibduUcEokC9WWJsUQVa6O4NKqgJSctESorWbSayijGD-3wB0VY4Hg:1neibv:qNGMiDKKe5DUJtEtS3jbm9WwIdxj9zV_QDselPETdKc','2022-04-27 19:25:03.593380'),('3tvss9tz4gv7p1mlom3m1qvb9o93j7hw','.eJxVjDEOwjAMRe-SGUUureKakZ0zRHZsSAE1UtNOFXenlTrA-t97f3WRlznHpdoUB3UX17jT7yacXjbuQJ88PopPZZynQfyu-INWfytq7-vh_h1krnmrEVIACibduUcEokC9WWJsUQVa6O4NKqgJSctESorWbSayijGD-3wB0VY4Hg:1nk2cY:0y3REHN27w024f5lo9cRg8YgLmRnoxp9r6l2GeiBZdk','2022-05-12 11:47:42.704994'),('5104utnbh2siipu9f38f5ydw94k6impq','.eJxVjDEOwjAMRe-SGUUureKakZ0zRHZsSAE1UtNOFXenlTrA-t97f3WRlznHpdoUB3UX17jT7yacXjbuQJ88PopPZZynQfyu-INWfytq7-vh_h1krnmrEVIACibduUcEokC9WWJsUQVa6O4NKqgJSctESorWbSayijGD-3wB0VY4Hg:1nQyBP:pJxvnh4yqR9pELFjduy5Vflsd4B1h4vFHlgF8mePHtY','2022-03-20 21:12:51.749586'),('a2vmsp9bi8d8rjf6oal28bvl93da05dw','.eJxVjDEOwjAMRe-SGUUureKakZ0zRHZsSAE1UtNOFXenlTrA-t97f3WRlznHpdoUB3UX17jT7yacXjbuQJ88PopPZZynQfyu-INWfytq7-vh_h1krnmrEVIACibduUcEokC9WWJsUQVa6O4NKqgJSctESorWbSayijGD-3wB0VY4Hg:1oDOnM:OKWQK-GMGZTlODVPWT6EYnXjtlgwNLfnVqkjYe4OVLQ','2022-08-01 11:20:12.100167'),('a9qw3rd3xfzuyhblpuykmcg6wq1jmkqa','.eJxVjDEOwjAMRe-SGUUureKakZ0zRHZsSAE1UtNOFXenlTrA-t97f3WRlznHpdoUB3UX17jT7yacXjbuQJ88PopPZZynQfyu-INWfytq7-vh_h1krnmrEVIACibduUcEokC9WWJsUQVa6O4NKqgJSctESorWbSayijGD-3wB0VY4Hg:1o4gxR:_pTbzQN7UaJNH5z_cv2VTCliVeNKwOEYadbr9jPWEFU','2022-07-08 10:54:37.334134'),('aqruknddcent9e487g4z81v1i6h7cbtw','.eJxVjDEOwjAMRe-SGUUureKakZ0zRHZsSAE1UtNOFXenlTrA-t97f3WRlznHpdoUB3UX17jT7yacXjbuQJ88PopPZZynQfyu-INWfytq7-vh_h1krnmrEVIACibduUcEokC9WWJsUQVa6O4NKqgJSctESorWbSayijGD-3wB0VY4Hg:1nY9cm:fBvZRSCRF22BTfSHO6uq-c8t0J-ICSRig75XfLqkkT0','2022-04-09 16:50:48.849224'),('c1n14nnsgy12n5jdelnyhs5ex77w9bgc','.eJxVjDEOwjAMRe-SGUUureKakZ0zRHZsSAE1UtNOFXenlTrA-t97f3WRlznHpdoUB3UX17jT7yacXjbuQJ88PopPZZynQfyu-INWfytq7-vh_h1krnmrEVIACibduUcEokC9WWJsUQVa6O4NKqgJSctESorWbSayijGD-3wB0VY4Hg:1oZrVj:LjpD1gKRfCpKoO4NVI_WKYeRNdeK7-4HPLysAmsvmTo','2022-10-02 10:26:51.372074'),('e256l3204m7j68f14yxh71rvagojevhe','.eJxVjDEOwjAMRe-SGUUureKakZ0zRHZsSAE1UtNOFXenlTrA-t97f3WRlznHpdoUB3UX17jT7yacXjbuQJ88PopPZZynQfyu-INWfytq7-vh_h1krnmrEVIACibduUcEokC9WWJsUQVa6O4NKqgJSctESorWbSayijGD-3wB0VY4Hg:1nDry0:ybUf0awI6OvwLYX8CdgmPyaWHHXe1avhEVflrMUADGo','2022-02-12 17:56:52.010600'),('j3gager1xbcp9mc2dgludna7h17b0y1x','.eJxVjDEOwjAMRe-SGUUureKakZ0zRHZsSAE1UtNOFXenlTrA-t97f3WRlznHpdoUB3UX17jT7yacXjbuQJ88PopPZZynQfyu-INWfytq7-vh_h1krnmrEVIACibduUcEokC9WWJsUQVa6O4NKqgJSctESorWbSayijGD-3wB0VY4Hg:1nZ87j:DEpdb4_8dXFcqjL2hHk943NdCt7ZNCkYBC-c7uH4v3A','2022-04-12 09:26:47.348338'),('kxbb5x7kbjhstwqlpqko50b65hms2kfu','.eJxVjDEOwjAMRe-SGUUureKakZ0zRHZsSAE1UtNOFXenlTrA-t97f3WRlznHpdoUB3UX17jT7yacXjbuQJ88PopPZZynQfyu-INWfytq7-vh_h1krnmrEVIACibduUcEokC9WWJsUQVa6O4NKqgJSctESorWbSayijGD-3wB0VY4Hg:1oPqIw:OMj0qSXuCCDv4M2am_pnH55ZeECybOCLSVk6-VAdoBk','2022-09-04 19:08:14.292962'),('m5dsnz5h1lfrj44wfpt1anrpf19k7zhn','.eJxVjDEOwjAMRe-SGUUureKakZ0zRHZsSAE1UtNOFXenlTrA-t97f3WRlznHpdoUB3UX17jT7yacXjbuQJ88PopPZZynQfyu-INWfytq7-vh_h1krnmrEVIACibduUcEokC9WWJsUQVa6O4NKqgJSctESorWbSayijGD-3wB0VY4Hg:1nOgYe:L54CA7JLCIwpcX5gCQVddaUC1_gKEzr076miOQNkzK8','2022-03-14 13:59:24.317105'),('ncaw443w9u479flu2c9g9i9j40r6prmq','.eJxVjDEOwjAMRe-SGUUureKakZ0zRHZsSAE1UtNOFXenlTrA-t97f3WRlznHpdoUB3UX17jT7yacXjbuQJ88PopPZZynQfyu-INWfytq7-vh_h1krnmrEVIACibduUcEokC9WWJsUQVa6O4NKqgJSctESorWbSayijGD-3wB0VY4Hg:1nTrAu:1p1_7X-wKk1Vhl2XTXbbW3ZeQ18n5Pn0g3kPj--5ZWM','2022-03-28 20:20:16.199867'),('oq844140h8takwn47hcpkt519dyfz86s','.eJxVjDEOwjAMRe-SGUUureKakZ0zRHZsSAE1UtNOFXenlTrA-t97f3WRlznHpdoUB3UX17jT7yacXjbuQJ88PopPZZynQfyu-INWfytq7-vh_h1krnmrEVIACibduUcEokC9WWJsUQVa6O4NKqgJSctESorWbSayijGD-3wB0VY4Hg:1nIwgC:O8HrQMCMe3sWUS6AUcW6Guov8Wv7me6W5XuJH9uR2bY','2022-02-26 17:59:28.435918'),('s29peboqj9ncqxpf5mvthjyxzsfq87fx','.eJxVjDEOwjAMRe-SGUUureKakZ0zRHZsSAE1UtNOFXenlTrA-t97f3WRlznHpdoUB3UX17jT7yacXjbuQJ88PopPZZynQfyu-INWfytq7-vh_h1krnmrEVIACibduUcEokC9WWJsUQVa6O4NKqgJSctESorWbSayijGD-3wB0VY4Hg:1nuaLL:aY9GmkJPoIevUGgAixkMCv6MUAU2vZFeMlXwDWGDmOI','2022-06-10 13:49:31.149510'),('wmfmjo8dt2pyuuf5bw9dgxqrxmqfy0he','.eJxVjDEOwjAMRe-SGUUureKakZ0zRHZsSAE1UtNOFXenlTrA-t97f3WRlznHpdoUB3UX17jT7yacXjbuQJ88PopPZZynQfyu-INWfytq7-vh_h1krnmrEVIACibduUcEokC9WWJsUQVa6O4NKqgJSctESorWbSayijGD-3wB0VY4Hg:1oUmS8:mgEd2wz62K99kf0A7k8ZKCQk2LxeVGlnBh5J4UTSoko','2022-09-18 10:02:08.485120'),('yiqy0fndal6ah2mdo7se2v5ppbszhby1','.eJxVjDEOwjAMRe-SGUUureKakZ0zRHZsSAE1UtNOFXenlTrA-t97f3WRlznHpdoUB3UX17jT7yacXjbuQJ88PopPZZynQfyu-INWfytq7-vh_h1krnmrEVIACibduUcEokC9WWJsUQVa6O4NKqgJSctESorWbSayijGD-3wB0VY4Hg:1nC7IB:Sx6X1uDp4hJxZA9JY2G70OQ8W_V-gxgvwXe_yYRbUVg','2022-02-07 21:54:27.421360');
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
  `name` varchar(100) NOT NULL,
  `definition` varchar(500) NOT NULL,
  `stream_id` bigint(20) DEFAULT NULL,
  `mtype` varchar(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `drawpad_mask_stream_id_c1668505_fk_streams_stream_id` (`stream_id`),
  CONSTRAINT `drawpad_mask_stream_id_c1668505_fk_streams_stream_id` FOREIGN KEY (`stream_id`) REFERENCES `streams_stream` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=244 DEFAULT CHARSET=utf8mb4;
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
  `school_id` bigint(20) NOT NULL,
  `hasarchive` tinyint(1) NOT NULL,
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
  `event_id` bigint(20) NOT NULL,
  `hasarchive` tinyint(1) NOT NULL,
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
  `eventer_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `eventers_evt_condition_eventer_id_81d1605a_fk_streams_stream_id` (`eventer_id`),
  CONSTRAINT `eventers_evt_condition_eventer_id_81d1605a_fk_streams_stream_id` FOREIGN KEY (`eventer_id`) REFERENCES `streams_stream` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=129 DEFAULT CHARSET=utf8mb4;
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
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4;
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
  `eve_alarm_email` varchar(255) NOT NULL,
  `eve_event_time_gap` int(11) NOT NULL,
  `eve_margin` int(11) NOT NULL,
  `eve_school` int(11) NOT NULL,
  `eve_all_predictions` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `streams_stream`
--

LOCK TABLES `streams_stream` WRITE;
/*!40000 ALTER TABLE `streams_stream` DISABLE KEYS */;
INSERT INTO `streams_stream` VALUES (1,1,'Havlickuv Brod','2020-01-01 00:00:00.000000','2022-01-24 22:23:57.820740',2,1,1280,720,0,8.072071962477995,2,'http://kamera.muhb.cz/mjpg/video.mjpg',1,0,1,60,0,4,23,-1,-1,2,2,0,7.6630219304642635,30,1,20,2,20,100,0,2,1,0,4.0679169206409584,'test@test.de',10,20,1,1);
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
  `tf_worker_id` bigint(20) NOT NULL,
  `ignore_checked` tinyint(1) NOT NULL,
  `donate_pics` tinyint(1) NOT NULL,
  `extra_runs` int(11) NOT NULL,
  `trainer_id` bigint(20) NOT NULL,
  `weight_boost` double NOT NULL,
  `weight_max` double NOT NULL,
  `weight_min` double NOT NULL,
  `patience` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tf_workers_school_tf_worker_id_3c7f9633_fk_tf_workers_worker_id` (`tf_worker_id`),
  KEY `tf_workers_school_trainer_id_171876a2_fk_trainers_trainer_id` (`trainer_id`),
  CONSTRAINT `tf_workers_school_tf_worker_id_3c7f9633_fk_tf_workers_worker_id` FOREIGN KEY (`tf_worker_id`) REFERENCES `tf_workers_worker` (`id`),
  CONSTRAINT `tf_workers_school_trainer_id_171876a2_fk_trainers_trainer_id` FOREIGN KEY (`trainer_id`) REFERENCES `trainers_trainer` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tf_workers_school`
--

LOCK TABLES `tf_workers_school` WRITE;
/*!40000 ALTER TABLE `tf_workers_school` DISABLE KEYS */;
INSERT INTO `tf_workers_school` VALUES (1,'Standard','data/models/c_model_1/',5000,'2022-07-14 20:13:27.039438',1,'1e-5','1e-5',1,'efficientnetv2b0',1,1,1,0,1,1,1,0.1,6);
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
  `gpu_sim_loading` double NOT NULL,
  `gpu_sim` double NOT NULL,
  `gpu_nr` int(11) NOT NULL,
  `savestats` double NOT NULL,
  `use_websocket` tinyint(1) NOT NULL,
  `wsserver` varchar(255) NOT NULL,
  `wspass` varchar(30) NOT NULL,
  `max_nr_models` int(11) NOT NULL,
  `timeout` double NOT NULL,
  `wsname` varchar(30) NOT NULL,
  `max_nr_clients` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tf_workers_worker`
--

LOCK TABLES `tf_workers_worker` WRITE;
/*!40000 ALTER TABLE `tf_workers_worker` DISABLE KEYS */;
INSERT INTO `tf_workers_worker` VALUES (1,1,'First',8,0,0,0,0,0,'wss://booker-hellerhoff.de:10443/','grmblwmpf',64,0.1,'ludger',20);
/*!40000 ALTER TABLE `tf_workers_worker` ENABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tools_setting`
--

LOCK TABLES `tools_setting` WRITE;
/*!40000 ALTER TABLE `tools_setting` DISABLE KEYS */;
INSERT INTO `tools_setting` VALUES (2,'loglevel','INFO','No Comment'),(5,'emulatestatic','0','No Comment'),(6,'version','0.6.1','No Comment'),(10,'recordingsurl','http://localhost/vclips/','No Comment'),(11,'local_trainer','0','No Comment');
/*!40000 ALTER TABLE `tools_setting` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trainers_epoch`
--

DROP TABLE IF EXISTS `trainers_epoch`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trainers_epoch` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `loss` double NOT NULL,
  `cmetrics` double NOT NULL,
  `val_loss` double NOT NULL,
  `val_cmetrics` double NOT NULL,
  `fit_id` int(11) NOT NULL,
  `hit100` double NOT NULL,
  `val_hit100` double NOT NULL,
  `seconds` double NOT NULL,
  `learning_rate` double NOT NULL,
  PRIMARY KEY (`id`),
  KEY `c_client_epoch_fit_id_14d2f630_fk_c_client_fit_id` (`fit_id`),
  CONSTRAINT `c_client_epoch_fit_id_14d2f630_fk_c_client_fit_id` FOREIGN KEY (`fit_id`) REFERENCES `trainers_fit` (`id`)
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
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `made` datetime(6) NOT NULL,
  `minutes` double NOT NULL,
  `school` int(11) NOT NULL,
  `epochs` int(11) NOT NULL,
  `nr_tr` int(11) NOT NULL,
  `nr_va` int(11) NOT NULL,
  `loss` double NOT NULL,
  `cmetrics` double NOT NULL,
  `val_loss` double NOT NULL,
  `val_cmetrics` double NOT NULL,
  `cputemp` double NOT NULL,
  `cpufan1` double NOT NULL,
  `cpufan2` double NOT NULL,
  `gputemp` double NOT NULL,
  `gpufan` double NOT NULL,
  `description` longtext NOT NULL,
  `hit100` double NOT NULL,
  `val_hit100` double NOT NULL,
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
  `name` varchar(256) NOT NULL,
  `t_type` int(11) NOT NULL,
  `active` tinyint(1) NOT NULL,
  `startworking` varchar(8) NOT NULL,
  `stopworking` varchar(8) NOT NULL,
  `gpu_nr` int(11) NOT NULL,
  `running` tinyint(1) NOT NULL,
  `wsserver` varchar(255) NOT NULL,
  `gpu_mem_limit` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trainers_trainer`
--

LOCK TABLES `trainers_trainer` WRITE;
/*!40000 ALTER TABLE `trainers_trainer` DISABLE KEYS */;
INSERT INTO `trainers_trainer` VALUES (1,'Trainer 1',3,1,'00:00:00','24:00:00',0,1,'wss://booker-hellerhoff.de:10443/',0);
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
  `made_by_id` int(11) DEFAULT NULL,
  `train_status` smallint(6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `trainers_trainframe_made_by_id_4562a1cb_fk_auth_user_id` (`made_by_id`),
  CONSTRAINT `trainers_trainframe_made_by_id_4562a1cb_fk_auth_user_id` FOREIGN KEY (`made_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=648 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trainers_trainframe`
--

LOCK TABLES `trainers_trainframe` WRITE;
/*!40000 ALTER TABLE `trainers_trainframe` DISABLE KEYS */;
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
  `name` varchar(100) NOT NULL,
  `made` datetime(6) NOT NULL,
  `school_id` bigint(20) DEFAULT NULL,
  `number` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `users_archive_school_id_75692b37_fk_tf_workers_school_id` (`school_id`),
  CONSTRAINT `users_archive_school_id_75692b37_fk_tf_workers_school_id` FOREIGN KEY (`school_id`) REFERENCES `tf_workers_school` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4;
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
  UNIQUE KEY `users_archive_user_archive_id_user_id_cc0c4189_uniq` (`archive_id`,`user_id`),
  KEY `users_archive_user_user_id_2000c010_fk_auth_user_id` (`user_id`),
  CONSTRAINT `users_archive_user_archive_id_f0594411_fk_users_archive_id` FOREIGN KEY (`archive_id`) REFERENCES `users_archive` (`id`),
  CONSTRAINT `users_archive_user_user_id_2000c010_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4;
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
  `counter` int(11) NOT NULL,
  `school_id` bigint(20) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `users_userinfo_school_id_3ee6112c_fk_tf_workers_school_id` (`school_id`),
  KEY `users_userinfo_user_id_6acffaf6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `users_userinfo_school_id_3ee6112c_fk_tf_workers_school_id` FOREIGN KEY (`school_id`) REFERENCES `tf_workers_school` (`id`),
  CONSTRAINT `users_userinfo_user_id_6acffaf6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_userinfo`
--

LOCK TABLES `users_userinfo` WRITE;
/*!40000 ALTER TABLE `users_userinfo` DISABLE KEYS */;
INSERT INTO `users_userinfo` VALUES (1,108,1,1);
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
-- Dumping routines for database 'CAM-AI_NEW'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2022-09-21  0:46:35
