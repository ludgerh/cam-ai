-- MariaDB dump 10.19  Distrib 10.11.3-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: 127.0.0.1    Database: CAM-AI_GIT
-- ------------------------------------------------------
-- Server version	10.11.3-MariaDB-1

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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `access_access_control`
--

LOCK TABLES `access_access_control` WRITE;
/*!40000 ALTER TABLE `access_access_control` DISABLE KEYS */;
INSERT INTO `access_access_control` VALUES
(1,'S',1,'U',0,'R');
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=109 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES
(1,'Can add log entry',1,'add_logentry'),
(2,'Can change log entry',1,'change_logentry'),
(3,'Can delete log entry',1,'delete_logentry'),
(4,'Can view log entry',1,'view_logentry'),
(5,'Can add permission',2,'add_permission'),
(6,'Can change permission',2,'change_permission'),
(7,'Can delete permission',2,'delete_permission'),
(8,'Can view permission',2,'view_permission'),
(9,'Can add group',3,'add_group'),
(10,'Can change group',3,'change_group'),
(11,'Can delete group',3,'delete_group'),
(12,'Can view group',3,'view_group'),
(13,'Can add user',4,'add_user'),
(14,'Can change user',4,'change_user'),
(15,'Can delete user',4,'delete_user'),
(16,'Can view user',4,'view_user'),
(17,'Can add content type',5,'add_contenttype'),
(18,'Can change content type',5,'change_contenttype'),
(19,'Can delete content type',5,'delete_contenttype'),
(20,'Can view content type',5,'view_contenttype'),
(21,'Can add session',6,'add_session'),
(22,'Can change session',6,'change_session'),
(23,'Can delete session',6,'delete_session'),
(24,'Can view session',6,'view_session'),
(25,'Can add camurl',7,'add_camurl'),
(26,'Can change camurl',7,'change_camurl'),
(27,'Can delete camurl',7,'delete_camurl'),
(28,'Can view camurl',7,'view_camurl'),
(29,'Can add setting',8,'add_setting'),
(30,'Can change setting',8,'change_setting'),
(31,'Can delete setting',8,'delete_setting'),
(32,'Can view setting',8,'view_setting'),
(33,'Can add view_log',9,'add_view_log'),
(34,'Can change view_log',9,'change_view_log'),
(35,'Can delete view_log',9,'delete_view_log'),
(36,'Can view view_log',9,'view_view_log'),
(37,'Can add stream',10,'add_stream'),
(38,'Can change stream',10,'change_stream'),
(39,'Can delete stream',10,'delete_stream'),
(40,'Can view stream',10,'view_stream'),
(41,'Can add access_control',11,'add_access_control'),
(42,'Can change access_control',11,'change_access_control'),
(43,'Can delete access_control',11,'delete_access_control'),
(44,'Can view access_control',11,'view_access_control'),
(45,'Can add event',12,'add_event'),
(46,'Can change event',12,'change_event'),
(47,'Can delete event',12,'delete_event'),
(48,'Can view event',12,'view_event'),
(49,'Can add evt_condition',13,'add_evt_condition'),
(50,'Can change evt_condition',13,'change_evt_condition'),
(51,'Can delete evt_condition',13,'delete_evt_condition'),
(52,'Can view evt_condition',13,'view_evt_condition'),
(53,'Can add event_frame',14,'add_event_frame'),
(54,'Can change event_frame',14,'change_event_frame'),
(55,'Can delete event_frame',14,'delete_event_frame'),
(56,'Can view event_frame',14,'view_event_frame'),
(57,'Can add worker',15,'add_worker'),
(58,'Can change worker',15,'change_worker'),
(59,'Can delete worker',15,'delete_worker'),
(60,'Can view worker',15,'view_worker'),
(61,'Can add school',16,'add_school'),
(62,'Can change school',16,'change_school'),
(63,'Can delete school',16,'delete_school'),
(64,'Can view school',16,'view_school'),
(65,'Can add mask',17,'add_mask'),
(66,'Can change mask',17,'change_mask'),
(67,'Can delete mask',17,'delete_mask'),
(68,'Can view mask',17,'view_mask'),
(69,'Can add fit',18,'add_fit'),
(70,'Can change fit',18,'change_fit'),
(71,'Can delete fit',18,'delete_fit'),
(72,'Can view fit',18,'view_fit'),
(73,'Can add trainer',19,'add_trainer'),
(74,'Can change trainer',19,'change_trainer'),
(75,'Can delete trainer',19,'delete_trainer'),
(76,'Can view trainer',19,'view_trainer'),
(77,'Can add trainframe',20,'add_trainframe'),
(78,'Can change trainframe',20,'change_trainframe'),
(79,'Can delete trainframe',20,'delete_trainframe'),
(80,'Can view trainframe',20,'view_trainframe'),
(81,'Can add epoch',21,'add_epoch'),
(82,'Can change epoch',21,'change_epoch'),
(83,'Can delete epoch',21,'delete_epoch'),
(84,'Can view epoch',21,'view_epoch'),
(85,'Can add tag',22,'add_tag'),
(86,'Can change tag',22,'change_tag'),
(87,'Can delete tag',22,'delete_tag'),
(88,'Can view tag',22,'view_tag'),
(89,'Can add userinfo',23,'add_userinfo'),
(90,'Can change userinfo',23,'change_userinfo'),
(91,'Can delete userinfo',23,'delete_userinfo'),
(92,'Can view userinfo',23,'view_userinfo'),
(93,'Can add archive',24,'add_archive'),
(94,'Can change archive',24,'change_archive'),
(95,'Can delete archive',24,'delete_archive'),
(96,'Can view archive',24,'view_archive'),
(97,'Can add client',25,'add_client'),
(98,'Can change client',25,'change_client'),
(99,'Can delete client',25,'delete_client'),
(100,'Can view client',25,'view_client'),
(101,'Can add client',26,'add_client'),
(102,'Can change client',26,'change_client'),
(103,'Can delete client',26,'delete_client'),
(104,'Can view client',26,'view_client'),
(105,'Can add token',27,'add_token'),
(106,'Can change token',27,'change_token'),
(107,'Can delete token',27,'delete_token'),
(108,'Can view token',27,'view_token');
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES
(1,'pbkdf2_sha256$390000$S1kU2slc9jyJIPerlg0Zke$XhcjiuIc1UQY9GpuGPFFE0YSDaM7blJVxsxSZqfBRZQ=','2023-01-04 11:57:48.600885',1,'admin','admin','admin','theo@tester.de',1,1,'2022-01-23 19:32:53.722000');
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES
(11,'access','access_control'),
(1,'admin','logentry'),
(3,'auth','group'),
(2,'auth','permission'),
(4,'auth','user'),
(5,'contenttypes','contenttype'),
(17,'drawpad','mask'),
(12,'eventers','event'),
(14,'eventers','event_frame'),
(13,'eventers','evt_condition'),
(22,'schools','tag'),
(6,'sessions','session'),
(10,'streams','stream'),
(16,'tf_workers','school'),
(15,'tf_workers','worker'),
(7,'tools','camurl'),
(8,'tools','setting'),
(27,'tools','token'),
(25,'trainers','client'),
(21,'trainers','epoch'),
(18,'trainers','fit'),
(19,'trainers','trainer'),
(20,'trainers','trainframe'),
(24,'users','archive'),
(23,'users','userinfo'),
(9,'viewers','view_log'),
(26,'ws_predictions','client');
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
) ENGINE=InnoDB AUTO_INCREMENT=58 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES
(1,'contenttypes','0001_initial','2022-11-04 18:56:57.246365'),
(2,'auth','0001_initial','2022-11-04 18:56:57.532126'),
(3,'admin','0001_initial','2022-11-04 18:56:57.599926'),
(4,'admin','0002_logentry_remove_auto_add','2022-11-04 18:56:57.607507'),
(5,'admin','0003_logentry_add_action_flag_choices','2022-11-04 18:56:57.616569'),
(6,'contenttypes','0002_remove_content_type_name','2022-11-04 18:56:57.669260'),
(7,'auth','0002_alter_permission_name_max_length','2022-11-04 18:56:57.725637'),
(8,'auth','0003_alter_user_email_max_length','2022-11-04 18:56:57.741043'),
(9,'auth','0004_alter_user_username_opts','2022-11-04 18:56:57.748792'),
(10,'auth','0005_alter_user_last_login_null','2022-11-04 18:56:57.773612'),
(11,'auth','0006_require_contenttypes_0002','2022-11-04 18:56:57.776596'),
(12,'auth','0007_alter_validators_add_error_messages','2022-11-04 18:56:57.786986'),
(13,'auth','0008_alter_user_username_max_length','2022-11-04 18:56:57.824373'),
(14,'auth','0009_alter_user_last_name_max_length','2022-11-04 18:56:57.858603'),
(15,'auth','0010_alter_group_name_max_length','2022-11-04 18:56:57.870261'),
(16,'auth','0011_update_proxy_permissions','2022-11-04 18:56:57.879404'),
(17,'auth','0012_alter_user_first_name_max_length','2022-11-04 18:56:57.918067'),
(18,'trainers','0001_initial','2022-11-04 18:56:58.033282'),
(19,'tf_workers','0001_initial','2022-11-04 18:56:58.114272'),
(20,'streams','0001_initial','2022-11-04 18:56:58.160346'),
(21,'drawpad','0001_initial','2022-11-04 18:56:58.202518'),
(22,'eventers','0001_initial','2022-11-04 18:56:58.355303'),
(23,'schools','0001_initial','2022-11-04 18:56:58.373325'),
(24,'sessions','0001_initial','2022-11-04 18:56:58.433658'),
(25,'tools','0001_initial','2022-11-04 18:56:58.461717'),
(26,'users','0001_initial','2022-11-04 18:56:58.680482'),
(27,'viewers','0001_initial','2022-11-04 18:56:58.693531'),
(28,'access','0001_initial','2022-11-04 20:00:10.465123'),
(29,'tf_workers','0002_alter_school_donate_pics_alter_school_l_rate_max_and_more','2022-11-09 15:00:42.185899'),
(30,'trainers','0002_trainer_wsname_trainer_wspass_alter_trainer_t_type','2022-11-09 15:00:42.207089'),
(31,'tf_workers','0003_alter_school_weight_boost_alter_worker_wsserver','2022-11-09 20:14:38.528761'),
(32,'trainers','0003_alter_trainer_wsserver','2022-11-09 20:14:38.535209'),
(33,'trainers','0004_client','2022-11-16 11:23:37.199017'),
(34,'ws_predictions','0001_initial','2022-11-16 11:23:37.214114'),
(35,'trainers','0005_client_comment','2022-11-16 11:30:51.758613'),
(36,'ws_predictions','0002_client_comment','2022-11-16 11:30:51.771806'),
(37,'tf_workers','0004_worker_wsadminpass','2022-11-16 11:47:03.108665'),
(38,'trainers','0006_trainer_wsadminpass','2022-11-16 11:47:03.119436'),
(39,'users','0002_remove_userinfo_counter_remove_userinfo_school_and_more','2022-11-16 16:32:31.594661'),
(40,'users','0003_alter_userinfo_client_nr','2022-11-16 16:42:28.317011'),
(41,'users','0004_remove_userinfo_client_nr','2022-11-16 16:47:30.398896'),
(42,'users','0005_userinfo_client_nr','2022-11-16 16:48:21.483471'),
(43,'tf_workers','0005_worker_wsid','2022-11-22 20:49:05.753087'),
(44,'trainers','0007_delete_client_remove_trainer_wsadminpass','2022-11-23 14:14:26.771639'),
(45,'streams','0002_stream_cam_max_x_view_stream_cam_min_x_view_and_more','2022-11-30 17:45:05.471974'),
(46,'tools','0002_token','2022-12-26 15:58:15.437771'),
(47,'tools','0003_token_valid','2022-12-26 16:18:15.215824'),
(48,'eventers','0002_remove_event_locktime','2022-12-27 11:02:48.422149'),
(49,'tools','0004_token_cat_token_idx_token_info','2022-12-27 16:13:54.106351'),
(50,'streams','0003_stream_cam_pause','2023-01-01 12:19:18.170560'),
(51,'tf_workers','0006_remove_worker_wsadminpass','2023-01-12 11:20:55.710029'),
(52,'users','0006_remove_userinfo_client_nr_userinfo_allowed_install_and_more','2023-01-12 11:20:55.848764'),
(53,'ws_predictions','0003_delete_client','2023-01-12 11:20:55.856973'),
(54,'users','0007_rename_allowed_install_userinfo_allowed_schools','2023-01-12 20:39:41.353068'),
(55,'users','0008_userinfo_used_schools','2023-01-12 20:40:08.173354'),
(56,'streams','0004_stream_det_scaledown','2023-01-22 20:26:23.707298'),
(57,'tf_workers','0007_alter_school_ignore_checked','2023-02-09 20:46:47.747657');
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
  `done` tinyint(1) NOT NULL,
  `videoclip` varchar(256) NOT NULL,
  `double` tinyint(1) NOT NULL,
  `hasarchive` tinyint(1) NOT NULL,
  `school_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `eventers_event_school_id_f65d815f_fk_tf_workers_school_id` (`school_id`),
  CONSTRAINT `eventers_event_school_id_f65d815f_fk_tf_workers_school_id` FOREIGN KEY (`school_id`) REFERENCES `tf_workers_school` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=23198 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=5984 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=60 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `schools_tag`
--

LOCK TABLES `schools_tag` WRITE;
/*!40000 ALTER TABLE `schools_tag` DISABLE KEYS */;
INSERT INTO `schools_tag` VALUES
(1,'night','Night',1,-1),
(2,'human','Human(s)',1,-1),
(3,'cat','Cat(s)',1,-1),
(4,'dog','Dog(s)',1,-1),
(5,'bird','Bird(s)',1,-1),
(6,'insect','Insect(s)',1,-1),
(7,'car','Car(s)',1,-1),
(8,'truck','Truck(s)',1,-1),
(9,'motorcycle','Motorcycle(s)',1,-1),
(10,'bicycle','Bicycle(s)',1,-1);
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
  `cam_pause` tinyint(1) NOT NULL,
  `det_scaledown` int(11) NOT NULL,
  `creator_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `streams_stream_eve_school_id_3e307b1b_fk_tf_workers_school_id` (`eve_school_id`),
  KEY `streams_stream_creator_id_6a9cc3b8_fk_auth_user_id` (`creator_id`),
  CONSTRAINT `streams_stream_creator_id_6a9cc3b8_fk_auth_user_id` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `streams_stream_eve_school_id_3e307b1b_fk_tf_workers_school_id` FOREIGN KEY (`eve_school_id`) REFERENCES `tf_workers_school` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
  `creator_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `tf_workers_school_tf_worker_id_3c7f9633_fk_tf_workers_worker_id` (`tf_worker_id`),
  KEY `tf_workers_school_trainer_id_171876a2_fk_trainers_trainer_id` (`trainer_id`),
  KEY `tf_workers_school_creator_id_b7d23651_fk_auth_user_id` (`creator_id`),
  CONSTRAINT `tf_workers_school_creator_id_b7d23651_fk_auth_user_id` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `tf_workers_school_tf_worker_id_3c7f9633_fk_tf_workers_worker_id` FOREIGN KEY (`tf_worker_id`) REFERENCES `tf_workers_worker` (`id`),
  CONSTRAINT `tf_workers_school_trainer_id_171876a2_fk_trainers_trainer_id` FOREIGN KEY (`trainer_id`) REFERENCES `trainers_trainer` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
  `wsid` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tf_workers_worker`
--

LOCK TABLES `tf_workers_worker` WRITE;
/*!40000 ALTER TABLE `tf_workers_worker` DISABLE KEYS */;
INSERT INTO `tf_workers_worker` VALUES
(1,1,'TF-Worker 1',8,0.1,64,20,0,-1,0,0,1,'wss://django.cam-ai.eu/','','',-1);
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tools_camurl`
--

LOCK TABLES `tools_camurl` WRITE;
/*!40000 ALTER TABLE `tools_camurl` DISABLE KEYS */;
INSERT INTO `tools_camurl` VALUES
(1,'Reolink RLC-410W','/bcs/channel0_main.bcs?channel=0&stream=1&user={user}&password={pass}');
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
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tools_setting`
--

LOCK TABLES `tools_setting` WRITE;
/*!40000 ALTER TABLE `tools_setting` DISABLE KEYS */;
INSERT INTO `tools_setting` VALUES
(1,'loglevel','INFO','No Comment'),
(2,'emulatestatic','0','No Comment'),
(3,'version','0.9.3','No Comment'),
(5,'local_trainer','0','No Comment'),
(6,'smtp_account','theo@tester.de','No Comment'),
(7,'smtp_password','yourpassword','No Comment'),
(8,'smtp_server','smtp.provider.com','No Comment'),
(9,'smtp_port','465','No Comment'),
(10,'smtp_email','theo@tester.de','No Comment'),
(11,'smtp_name','CAM-AI Emailer','No Comment'),
(12,'system_number','-1','No Comment'),
(13,'deletethreshold','0','In Percent');
/*!40000 ALTER TABLE `tools_setting` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tools_token`
--

DROP TABLE IF EXISTS `tools_token`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tools_token` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `passwd` varchar(20) NOT NULL,
  `made` datetime(6) NOT NULL,
  `count` int(11) NOT NULL,
  `valid` tinyint(1) NOT NULL,
  `cat` varchar(3) NOT NULL,
  `idx` int(11) NOT NULL,
  `info` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=201 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tools_token`
--

LOCK TABLES `tools_token` WRITE;
/*!40000 ALTER TABLE `tools_token` DISABLE KEYS */;
/*!40000 ALTER TABLE `tools_token` ENABLE KEYS */;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trainers_trainer`
--

LOCK TABLES `trainers_trainer` WRITE;
/*!40000 ALTER TABLE `trainers_trainer` DISABLE KEYS */;
INSERT INTO `trainers_trainer` VALUES
(1,0,'Trainer 1',3,0,0,'00:00:00','24:00:00',1,'wss://django.cam-ai.eu/','','');
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
) ENGINE=InnoDB AUTO_INCREMENT=1150 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
  `number` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `made` datetime(6) NOT NULL,
  `school_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `users_archive_school_id_75692b37_fk_tf_workers_school_id` (`school_id`),
  CONSTRAINT `users_archive_school_id_75692b37_fk_tf_workers_school_id` FOREIGN KEY (`school_id`) REFERENCES `tf_workers_school` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
  `allowed_schools` int(11) NOT NULL,
  `deadline` datetime(6) NOT NULL,
  `made` datetime(6) NOT NULL,
  `pay_tokens` int(11) NOT NULL,
  `used_schools` int(11) NOT NULL,
  `allowed_streams` int(11) NOT NULL,
  `used_streams` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `users_userinfo_user_id_6acffaf6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `users_userinfo_user_id_6acffaf6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_userinfo`
--

LOCK TABLES `users_userinfo` WRITE;
/*!40000 ALTER TABLE `users_userinfo` DISABLE KEYS */;
INSERT INTO `users_userinfo` VALUES
(1,1,2,'2100-01-01 00:00:00.000000','2023-01-12 11:20:55.834211',0,1,1,0);
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
) ENGINE=InnoDB AUTO_INCREMENT=1034 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `viewers_view_log`
--

LOCK TABLES `viewers_view_log` WRITE;
/*!40000 ALTER TABLE `viewers_view_log` DISABLE KEYS */;
INSERT INTO `viewers_view_log` VALUES
(201,'C',8,'2022-11-22 22:00:46.420468','2022-11-22 22:00:53.225068',1,0),
(202,'E',8,'2022-11-22 22:00:53.806943','2022-11-22 22:01:01.910850',1,0),
(203,'E',8,'2022-11-22 22:01:02.470652','2022-11-22 22:01:02.470663',1,1),
(204,'E',8,'2022-11-22 22:01:47.753715','2022-11-22 22:02:15.717300',1,0),
(205,'E',8,'2022-11-22 22:02:16.291567','2022-11-22 22:02:16.291577',1,1),
(206,'E',8,'2022-11-22 22:04:26.041581','2022-11-22 22:05:00.700430',1,0),
(207,'E',8,'2022-11-22 22:05:01.261224','2022-11-22 22:05:01.261229',1,1),
(208,'E',8,'2022-11-22 22:07:31.927816','2022-11-22 22:07:59.399921',1,0),
(209,'E',8,'2022-11-22 22:07:59.986859','2022-11-22 22:07:59.986864',1,1),
(210,'E',8,'2022-11-22 22:13:04.179206','2022-11-22 22:13:04.179213',1,1),
(211,'E',8,'2022-11-22 22:14:25.747085','2022-11-22 22:16:17.303966',1,0),
(212,'E',8,'2022-11-22 22:16:19.005897','2022-11-22 22:16:35.419813',1,0),
(213,'E',8,'2022-11-22 22:16:36.483458','2022-11-22 22:16:44.888722',1,0),
(214,'E',8,'2022-11-22 22:16:46.071016','2022-11-22 22:24:03.543594',1,0),
(215,'E',8,'2022-11-22 22:24:04.094066','2022-11-22 22:24:04.094073',1,1),
(216,'E',8,'2022-11-22 22:24:47.638929','2022-11-22 22:24:47.638935',1,1),
(217,'E',8,'2022-11-22 22:27:07.190744','2022-11-22 22:27:07.191304',1,1),
(218,'E',8,'2022-11-22 22:35:28.954213','2022-11-22 22:35:28.954220',1,1),
(219,'E',8,'2022-11-22 22:36:54.787768','2022-11-22 22:36:54.787774',1,1),
(220,'E',8,'2022-11-22 22:38:31.720017','2022-11-22 22:38:31.720026',1,1),
(221,'E',8,'2022-11-22 22:43:04.023033','2022-11-22 22:43:39.386195',1,0),
(222,'E',8,'2022-11-22 22:43:39.890072','2022-11-22 22:43:39.890079',1,1),
(223,'E',8,'2022-11-22 22:44:40.764111','2022-11-22 22:45:54.157376',1,0),
(224,'E',8,'2022-11-22 22:45:54.574912','2022-11-22 22:45:54.574917',1,1),
(225,'E',8,'2022-11-22 22:48:04.984120','2022-11-22 22:48:04.984126',1,1),
(226,'E',8,'2022-11-22 22:51:07.209266','2022-11-22 22:51:07.209276',1,1),
(227,'E',8,'2022-11-22 22:54:32.810950','2022-11-22 22:55:08.194512',1,0),
(228,'E',8,'2022-11-22 22:55:08.877848','2022-11-22 22:55:25.401138',1,0),
(229,'E',8,'2022-11-22 22:55:25.910966','2022-11-22 22:55:25.910978',1,1),
(230,'E',8,'2022-11-22 22:57:17.980576','2022-11-22 22:57:55.567010',1,0),
(231,'D',7,'2022-11-22 22:57:56.199626','2022-11-22 22:58:48.470233',1,0),
(232,'D',7,'2022-11-22 22:58:49.472591','2022-11-22 22:58:49.472598',1,1),
(233,'C',7,'2022-11-22 23:08:19.211644','2022-11-22 23:08:34.701548',1,0),
(234,'C',8,'2022-11-22 23:08:19.245386','2022-11-22 23:08:34.705853',1,0),
(235,'C',7,'2022-11-22 23:11:12.735428','2022-11-22 23:11:12.735433',1,1),
(236,'C',8,'2022-11-22 23:11:12.749511','2022-11-22 23:11:12.749517',1,1),
(237,'C',9,'2022-11-22 23:11:12.754840','2022-11-22 23:11:12.754845',1,1),
(238,'C',7,'2022-11-23 13:42:07.367422','2022-11-23 13:42:12.631015',1,0),
(239,'C',7,'2022-11-23 13:42:13.385866','2022-11-23 13:42:18.293080',1,0),
(240,'D',7,'2022-11-23 13:42:18.831215','2022-11-23 13:42:23.087271',1,0),
(241,'E',7,'2022-11-23 13:42:23.650236','2022-11-23 13:42:23.650240',1,1),
(242,'E',7,'2022-11-23 13:46:18.517406','2022-11-23 13:46:18.517416',1,1),
(243,'E',7,'2022-11-23 13:46:44.444586','2022-11-23 13:47:37.542417',1,0),
(244,'C',7,'2022-11-23 13:47:47.567145','2022-11-23 13:47:51.335672',1,0),
(245,'C',7,'2022-11-23 13:47:57.517801','2022-11-23 13:48:01.015681',1,0),
(246,'D',7,'2022-11-23 13:48:01.409619','2022-11-23 13:48:04.031740',1,0),
(247,'D',7,'2022-11-23 13:48:04.479177','2022-11-23 13:48:07.911885',1,0),
(248,'C',7,'2022-11-23 13:48:08.294987','2022-11-23 13:48:10.394792',1,0),
(249,'C',7,'2022-11-23 13:48:10.858350','2022-11-23 13:48:18.127143',1,0),
(250,'C',7,'2022-11-23 13:55:05.861449','2022-11-23 13:55:10.686035',1,0),
(251,'C',7,'2022-11-23 13:58:03.040436','2022-11-23 13:58:10.097717',1,0),
(252,'C',7,'2022-11-23 14:04:40.518903','2022-11-23 14:04:49.407984',1,0),
(253,'C',7,'2022-11-23 14:15:03.827185','2022-11-23 14:15:16.021367',1,0),
(254,'C',7,'2022-11-23 14:17:15.753713','2022-11-23 14:17:15.753719',1,1),
(255,'E',1,'2022-11-23 14:52:13.310353','2022-11-23 14:53:55.851547',1,0),
(256,'C',1,'2022-11-23 14:54:01.289792','2022-11-23 14:54:03.334656',1,0),
(257,'C',1,'2022-11-23 14:54:05.849901','2022-11-23 14:54:07.788365',1,0),
(258,'E',1,'2022-11-23 14:54:08.203791','2022-11-23 14:54:18.538765',1,0),
(259,'E',1,'2022-11-23 14:54:18.904245','2022-11-23 14:55:02.397644',1,0),
(260,'C',1,'2022-11-23 14:55:05.774359','2022-11-23 14:55:09.390739',1,0),
(261,'C',1,'2022-11-23 14:55:11.522827','2022-11-23 14:55:13.357857',1,0),
(262,'E',1,'2022-11-23 14:55:13.709583','2022-11-23 14:55:36.284235',1,0),
(263,'E',1,'2022-11-23 14:56:01.293374','2022-11-23 14:56:32.735863',1,0),
(264,'E',1,'2022-11-23 14:56:40.242661','2022-11-23 14:57:19.099576',1,0),
(265,'C',1,'2022-11-23 14:57:26.651481','2022-11-23 14:57:29.030907',1,0),
(266,'C',1,'2022-11-23 14:57:43.400008','2022-11-23 14:57:46.539021',1,0),
(267,'C',1,'2022-11-23 14:58:52.911919','2022-11-23 14:58:52.911926',1,1),
(268,'C',1,'2022-11-23 20:19:32.537653','2022-11-23 20:19:45.115064',1,0),
(269,'E',1,'2022-11-23 20:19:45.620671','2022-11-23 20:21:21.763893',1,0),
(270,'C',1,'2022-11-23 20:27:58.891512','2022-11-23 20:28:09.624647',1,0),
(271,'E',1,'2022-11-23 20:28:10.073317','2022-11-23 20:28:14.608127',1,0),
(272,'C',1,'2022-11-23 20:58:57.089867','2022-11-23 20:59:10.817528',1,0),
(273,'C',1,'2022-11-23 21:02:56.268149','2022-11-23 21:03:07.316717',1,0),
(274,'C',1,'2022-11-25 18:51:12.456511','2022-11-25 18:51:16.254757',1,0),
(275,'C',1,'2022-11-25 18:54:42.179435','2022-11-25 18:54:44.743760',1,0),
(276,'E',1,'2022-11-25 18:54:45.378507','2022-11-25 18:55:16.724957',1,0),
(277,'E',1,'2022-11-25 18:55:20.308325','2022-11-25 18:56:23.920534',1,0),
(278,'C',1,'2022-11-25 18:56:53.171217','2022-11-25 18:56:55.574255',1,0),
(279,'E',1,'2022-11-25 18:56:56.013819','2022-11-25 18:57:07.342578',1,0),
(280,'C',1,'2022-11-25 18:57:41.081815','2022-11-25 18:57:43.649521',1,0),
(281,'E',1,'2022-11-25 18:57:44.052513','2022-11-25 18:57:57.767629',1,0),
(282,'C',1,'2022-11-25 18:58:09.945851','2022-11-25 18:58:12.162021',1,0),
(283,'C',1,'2022-11-25 18:58:20.896337','2022-11-25 18:58:21.526467',1,0),
(284,'E',1,'2022-11-25 18:58:22.572646','2022-11-25 18:59:24.244210',1,0),
(285,'C',1,'2022-11-25 18:59:53.772315','2022-11-25 18:59:55.728575',1,0),
(286,'C',1,'2022-11-27 21:37:53.490124','2022-11-27 21:38:00.544333',1,0),
(287,'C',1,'2022-11-27 21:38:00.954015','2022-11-27 21:38:25.002563',1,0),
(288,'E',1,'2022-11-27 21:38:25.582288','2022-11-27 21:38:58.014901',1,0),
(289,'E',1,'2022-11-27 21:43:55.565164','2022-11-27 21:44:10.819576',1,0),
(290,'C',1,'2022-11-28 14:51:57.016061','2022-11-28 14:52:11.174294',1,0),
(291,'C',1,'2022-11-28 14:52:11.889725','2022-11-28 14:52:11.889731',1,1),
(292,'C',1,'2022-11-28 15:05:49.540631','2022-11-28 15:05:59.723961',1,0),
(293,'C',1,'2022-11-28 15:06:00.215554','2022-11-28 15:06:10.125260',1,0),
(294,'C',1,'2022-11-28 15:06:27.822770','2022-11-28 15:06:35.369747',1,0),
(295,'C',1,'2022-11-28 15:06:48.283073','2022-11-28 15:06:53.391961',1,0),
(296,'E',1,'2022-11-28 15:06:53.818151','2022-11-28 15:07:54.998609',1,0),
(297,'C',1,'2022-11-28 15:09:27.810009','2022-11-28 15:09:29.909505',1,0),
(298,'E',1,'2022-11-28 15:09:30.313804','2022-11-28 15:09:30.313809',1,1),
(299,'C',1,'2022-11-28 15:21:40.091385','2022-11-28 15:21:42.642490',1,0),
(300,'C',1,'2022-11-28 15:21:43.074088','2022-11-28 15:21:43.074095',1,1),
(301,'C',1,'2022-11-28 15:23:34.198344','2022-11-28 15:23:34.198349',1,1),
(302,'C',1,'2022-11-28 15:24:05.943746','2022-11-28 15:24:05.943753',1,1),
(303,'C',1,'2022-11-28 15:24:53.676888','2022-11-28 15:25:10.043727',1,0),
(304,'C',1,'2022-11-28 16:44:14.820744','2022-11-28 16:44:18.651678',1,0),
(305,'C',1,'2022-11-28 16:44:46.448120','2022-11-28 16:44:57.782427',1,0),
(306,'C',1,'2022-11-28 16:45:07.213440','2022-11-28 16:45:09.103846',1,0),
(307,'C',1,'2022-11-28 16:45:22.236320','2022-11-28 16:45:24.199619',1,0),
(308,'C',1,'2022-11-28 16:48:33.113151','2022-11-28 16:48:36.621589',1,0),
(309,'C',1,'2022-11-28 20:34:02.462447','2022-11-28 20:34:04.586326',1,0),
(310,'C',1,'2022-11-28 20:35:55.439972','2022-11-28 20:35:59.156319',1,0),
(311,'C',1,'2022-11-29 08:33:48.884621','2022-11-29 08:34:06.230431',1,0),
(312,'C',1,'2022-11-29 08:34:06.761611','2022-11-29 08:34:06.761617',1,1),
(313,'C',1,'2022-11-29 09:08:58.114793','2022-11-29 09:08:58.114799',1,1),
(314,'C',1,'2022-11-29 09:10:38.441329','2022-11-29 09:10:38.441334',1,1),
(315,'C',1,'2022-11-29 09:15:22.871289','2022-11-29 09:15:22.871295',1,1),
(316,'C',1,'2022-11-29 09:17:03.350147','2022-11-29 09:17:03.350151',1,1),
(317,'C',1,'2022-11-29 09:19:14.505673','2022-11-29 09:19:14.505679',1,1),
(318,'C',1,'2022-11-29 09:20:10.875489','2022-11-29 09:20:10.875494',1,1),
(319,'C',1,'2022-11-29 09:25:14.297276','2022-11-29 09:25:56.462457',1,0),
(320,'C',1,'2022-11-29 09:25:56.751160','2022-11-29 09:26:16.150854',1,0),
(321,'C',1,'2022-11-29 09:26:16.506185','2022-11-29 09:26:46.627796',1,0),
(322,'C',1,'2022-11-29 09:26:46.877290','2022-11-29 09:26:46.877297',1,1),
(323,'C',1,'2022-11-29 09:32:27.912946','2022-11-29 09:32:30.123390',1,0),
(324,'C',1,'2022-11-29 09:32:51.502456','2022-11-29 09:32:55.063432',1,0),
(325,'C',1,'2022-11-29 09:32:55.481926','2022-11-29 09:32:55.481933',1,1),
(326,'C',1,'2022-11-29 09:34:58.753403','2022-11-29 09:35:44.735971',1,0),
(327,'C',1,'2022-11-29 09:35:45.044003','2022-11-29 09:36:03.103436',1,0),
(328,'C',1,'2022-11-29 09:36:03.487403','2022-11-29 09:36:03.487409',1,1),
(329,'C',1,'2022-11-29 09:38:37.213987','2022-11-29 09:38:37.213994',1,1),
(330,'C',1,'2022-11-29 09:39:06.311536','2022-11-29 09:39:06.311542',1,1),
(331,'C',1,'2022-11-29 09:39:54.632316','2022-11-29 09:40:27.856061',1,0),
(332,'C',1,'2022-11-29 09:40:28.226817','2022-11-29 09:40:28.226823',1,1),
(333,'C',1,'2022-11-29 09:42:35.146329','2022-11-29 09:42:35.146334',1,1),
(334,'C',1,'2022-11-29 09:44:46.599948','2022-11-29 09:44:46.599955',1,1),
(335,'C',1,'2022-11-29 09:46:05.130561','2022-11-29 09:46:05.130566',1,1),
(336,'C',1,'2022-11-29 09:47:53.069817','2022-11-29 09:47:53.069822',1,1),
(337,'C',1,'2022-11-29 09:49:24.616754','2022-11-29 09:49:24.616760',1,1),
(338,'C',1,'2022-11-29 09:56:08.543187','2022-11-29 09:56:08.543193',1,1),
(339,'C',1,'2022-11-29 09:57:15.305260','2022-11-29 09:57:15.305264',1,1),
(340,'C',1,'2022-11-29 09:57:57.827838','2022-11-29 09:57:57.827845',1,1),
(341,'C',1,'2022-11-29 09:58:35.841277','2022-11-29 09:58:35.841283',1,1),
(342,'C',1,'2022-11-29 10:05:56.324435','2022-11-29 10:05:56.324439',1,1),
(343,'C',1,'2022-11-29 10:07:11.414527','2022-11-29 10:07:11.414533',1,1),
(344,'C',1,'2022-11-29 10:13:56.739561','2022-11-29 10:13:56.739568',1,1),
(345,'C',1,'2022-11-29 10:15:37.167022','2022-11-29 10:15:37.167031',1,1),
(346,'C',1,'2022-11-29 10:17:49.318313','2022-11-29 10:17:49.318319',1,1),
(347,'C',1,'2022-11-29 10:20:25.592062','2022-11-29 10:20:25.592067',1,1),
(348,'C',1,'2022-11-29 10:21:49.046837','2022-11-29 10:21:49.046843',1,1),
(349,'C',1,'2022-11-29 10:24:24.837257','2022-11-29 10:24:24.837268',1,1),
(350,'C',1,'2022-11-29 10:24:52.271454','2022-11-29 10:24:52.271461',1,1),
(351,'C',1,'2022-11-29 10:25:29.426360','2022-11-29 10:25:29.426367',1,1),
(352,'C',1,'2022-11-29 10:26:47.008140','2022-11-29 10:26:47.008146',1,1),
(353,'C',1,'2022-11-29 10:27:33.725536','2022-11-29 10:27:33.725542',1,1),
(354,'C',1,'2022-11-29 10:40:35.844227','2022-11-29 10:40:58.670015',1,0),
(355,'C',1,'2022-11-29 10:41:04.897003','2022-11-29 10:41:20.980117',1,0),
(356,'C',1,'2022-11-29 10:41:22.049298','2022-11-29 10:41:22.049303',1,1),
(357,'C',1,'2022-11-29 10:43:40.143677','2022-11-29 10:43:40.143685',1,1),
(358,'C',1,'2022-11-29 10:44:41.040288','2022-11-29 10:44:41.040300',1,1),
(359,'C',1,'2022-11-29 10:47:18.743903','2022-11-29 10:47:18.743910',1,1),
(360,'C',1,'2022-11-29 10:48:00.707030','2022-11-29 10:48:00.707040',1,1),
(361,'C',1,'2022-11-29 10:49:07.998556','2022-11-29 10:49:07.998566',1,1),
(362,'C',1,'2022-11-29 10:56:10.199881','2022-11-29 10:56:10.199888',1,1),
(363,'C',1,'2022-11-29 10:58:48.484077','2022-11-29 10:58:48.484081',1,1),
(364,'C',1,'2022-11-29 10:59:50.346674','2022-11-29 10:59:50.346680',1,1),
(365,'C',1,'2022-11-29 11:02:25.387510','2022-11-29 11:02:25.387518',1,1),
(366,'C',1,'2022-11-29 11:13:17.872316','2022-11-29 11:13:17.872320',1,1),
(367,'C',1,'2022-11-29 11:17:21.492816','2022-11-29 11:17:21.492821',1,1),
(368,'C',1,'2022-11-29 11:17:57.856861','2022-11-29 11:17:57.856867',1,1),
(369,'C',1,'2022-11-29 12:25:42.242323','2022-11-29 12:25:45.338467',1,0),
(370,'C',1,'2022-11-29 12:25:45.718620','2022-11-29 12:26:48.573230',1,0),
(371,'C',1,'2022-11-29 12:26:49.451505','2022-11-29 12:26:49.451511',1,1),
(372,'C',1,'2022-11-29 12:28:58.738578','2022-11-29 12:29:10.292805',1,0),
(373,'C',1,'2022-11-29 12:29:11.553763','2022-11-29 12:29:11.553773',1,1),
(374,'C',1,'2022-11-29 13:07:43.480216','2022-11-29 13:07:43.480220',1,1),
(375,'C',1,'2022-11-29 14:41:03.537655','2022-11-29 14:41:03.537659',1,1),
(376,'C',1,'2022-11-29 14:42:27.038111','2022-11-29 14:43:14.281832',1,0),
(377,'C',1,'2022-11-29 14:43:15.274046','2022-11-29 14:43:15.274053',1,1),
(378,'C',1,'2022-11-29 14:49:06.197668','2022-11-29 14:49:06.197672',1,1),
(379,'C',1,'2022-11-29 14:50:23.055263','2022-11-29 14:50:23.055269',1,1),
(380,'C',1,'2022-11-29 14:51:40.137464','2022-11-29 14:51:40.137469',1,1),
(381,'C',1,'2022-11-29 14:52:35.365475','2022-11-29 14:52:35.365482',1,1),
(382,'C',1,'2022-11-29 14:55:12.416338','2022-11-29 14:55:12.416345',1,1),
(383,'C',1,'2022-11-29 14:57:45.019736','2022-11-29 14:57:45.019741',1,1),
(384,'C',1,'2022-11-29 15:02:58.400993','2022-11-29 15:02:58.400997',1,1),
(385,'C',1,'2022-11-29 15:03:40.730488','2022-11-29 15:03:40.730495',1,1),
(386,'C',1,'2022-11-29 15:04:38.563643','2022-11-29 15:04:38.563650',1,1),
(387,'C',1,'2022-11-29 15:10:33.351402','2022-11-29 15:10:33.351410',1,1),
(388,'C',1,'2022-11-29 15:18:14.894191','2022-11-29 15:18:14.894198',1,1),
(389,'C',1,'2022-11-29 15:18:42.246830','2022-11-29 15:18:42.246836',1,1),
(390,'C',1,'2022-11-29 15:19:36.839383','2022-11-29 15:19:36.839388',1,1),
(391,'C',1,'2022-11-29 15:23:47.859754','2022-11-29 15:23:47.859758',1,1),
(392,'C',1,'2022-11-29 16:30:51.177920','2022-11-29 16:30:51.177926',1,1),
(393,'C',1,'2022-11-29 16:38:56.133156','2022-11-29 16:38:56.133160',1,1),
(394,'C',1,'2022-11-29 16:48:26.593528','2022-11-29 16:48:26.593534',1,1),
(395,'C',1,'2022-11-29 16:52:53.408163','2022-11-29 16:52:53.408168',1,1),
(396,'C',1,'2022-11-29 17:02:24.949772','2022-11-29 17:02:24.949776',1,1),
(397,'C',1,'2022-11-29 17:55:59.935789','2022-11-29 17:56:20.685876',1,0),
(398,'C',1,'2022-11-29 19:48:48.424890','2022-11-29 19:48:48.424895',1,1),
(399,'C',1,'2022-11-29 19:49:31.838202','2022-11-29 19:49:31.838210',1,1),
(400,'C',1,'2022-11-29 19:50:30.332655','2022-11-29 19:50:30.332672',1,1),
(401,'C',1,'2022-11-29 20:13:24.316718','2022-11-29 20:13:24.316723',1,1),
(402,'C',1,'2022-11-29 20:14:19.964485','2022-11-29 20:14:19.964490',1,1),
(403,'C',1,'2022-11-29 20:14:59.155885','2022-11-29 20:14:59.155891',1,1),
(404,'C',1,'2022-11-29 20:17:06.828789','2022-11-29 20:17:06.828794',1,1),
(405,'C',1,'2022-11-29 20:18:22.690873','2022-11-29 20:18:22.690878',1,1),
(406,'C',1,'2022-11-29 20:20:43.212681','2022-11-29 20:20:43.212686',1,1),
(407,'C',1,'2022-11-29 20:23:07.025488','2022-11-29 20:23:09.731971',1,0),
(408,'C',1,'2022-11-29 20:23:10.099785','2022-11-29 20:23:22.198788',1,0),
(409,'C',1,'2022-11-29 20:23:22.775571','2022-11-29 20:23:31.203693',1,0),
(410,'C',1,'2022-11-29 20:23:31.602036','2022-11-29 20:24:21.888890',1,0),
(411,'C',1,'2022-11-29 20:24:22.610284','2022-11-29 20:24:24.831560',1,0),
(412,'C',1,'2022-11-29 20:24:25.287324','2022-11-29 20:24:25.287329',1,1),
(413,'C',1,'2022-11-29 20:24:55.233786','2022-11-29 20:25:10.592975',1,0),
(414,'C',1,'2022-11-29 20:25:11.176174','2022-11-29 20:25:13.593750',1,0),
(415,'C',1,'2022-11-29 20:25:14.140054','2022-11-29 20:25:14.140061',1,1),
(416,'C',1,'2022-11-29 20:26:39.785346','2022-11-29 20:26:50.252629',1,0),
(417,'C',1,'2022-11-29 20:26:50.771184','2022-11-29 20:26:50.771191',1,1),
(418,'C',1,'2022-11-29 20:30:56.036364','2022-11-29 20:30:56.036370',1,1),
(419,'C',1,'2022-11-29 20:37:29.033837','2022-11-29 20:37:29.033842',1,1),
(420,'C',1,'2022-11-29 20:38:51.690160','2022-11-29 20:38:51.690173',1,1),
(421,'C',1,'2022-11-29 20:44:00.568094','2022-11-29 20:44:00.568102',1,1),
(422,'C',1,'2022-11-29 20:44:52.074542','2022-11-29 20:44:52.074548',1,1),
(423,'C',1,'2022-11-29 21:19:56.496930','2022-11-29 21:20:56.089145',1,0),
(424,'D',1,'2022-11-29 21:20:56.931533','2022-11-29 21:20:56.931540',1,1),
(425,'D',1,'2022-11-29 21:26:16.648999','2022-11-29 21:26:16.649004',1,1),
(426,'D',1,'2022-11-29 22:05:54.168058','2022-11-29 22:06:03.670540',1,0),
(427,'C',1,'2022-11-29 22:06:04.655010','2022-11-29 22:06:04.655017',1,1),
(428,'C',1,'2022-11-29 22:09:00.533909','2022-11-29 22:09:00.533913',1,1),
(429,'C',1,'2022-11-29 22:25:18.708375','2022-11-29 22:25:18.708380',1,1),
(430,'C',1,'2022-11-29 22:26:28.073810','2022-11-29 22:26:28.073816',1,1),
(431,'C',1,'2022-11-29 22:28:09.970558','2022-11-29 22:28:09.970565',1,1),
(432,'C',1,'2022-11-29 22:30:42.418603','2022-11-29 22:30:53.328822',1,0),
(433,'D',1,'2022-11-29 22:30:54.138733','2022-11-29 22:30:54.138739',1,1),
(434,'C',1,'2022-11-29 22:45:49.796262','2022-11-29 22:45:49.796272',1,1),
(435,'C',1,'2022-11-29 22:51:33.186309','2022-11-29 22:51:53.941851',1,0),
(436,'D',1,'2022-11-29 22:51:54.608586','2022-11-29 22:52:28.118905',1,0),
(437,'D',1,'2022-11-29 22:52:28.817160','2022-11-29 22:52:28.817177',1,1),
(438,'D',1,'2022-11-29 22:59:44.217073','2022-11-29 22:59:44.217080',1,1),
(439,'D',1,'2022-11-29 23:00:27.766130','2022-11-29 23:00:27.766143',1,1),
(440,'C',1,'2022-11-30 10:19:27.814148','2022-11-30 10:19:30.854815',1,0),
(441,'C',1,'2022-11-30 10:19:31.222832','2022-11-30 10:19:31.222838',1,1),
(442,'C',1,'2022-11-30 10:46:35.060491','2022-11-30 10:47:58.098921',1,0),
(443,'D',1,'2022-11-30 10:47:58.614226','2022-11-30 10:49:00.202349',1,0),
(444,'D',1,'2022-11-30 10:49:00.642235','2022-11-30 10:49:00.642242',1,1),
(445,'C',1,'2022-11-30 11:25:21.901098','2022-11-30 11:26:19.135782',1,0),
(446,'C',1,'2022-11-30 11:26:20.838055','2022-11-30 11:26:28.561061',1,0),
(447,'C',1,'2022-11-30 11:26:29.286225','2022-11-30 11:26:39.913800',1,0),
(448,'D',1,'2022-11-30 11:26:40.680931','2022-11-30 11:26:46.597192',1,0),
(449,'E',1,'2022-11-30 11:26:47.648997','2022-11-30 11:26:47.649005',1,1),
(450,'D',1,'2022-11-30 11:29:22.792901','2022-11-30 11:29:22.792909',1,1),
(451,'D',1,'2022-11-30 11:33:15.834270','2022-11-30 11:33:15.834276',1,1),
(452,'C',1,'2022-11-30 16:00:36.788673','2022-11-30 16:00:52.690430',1,0),
(453,'C',1,'2022-11-30 16:26:17.188286','2022-11-30 16:26:17.188297',1,1),
(454,'C',1,'2022-11-30 16:27:17.316192','2022-11-30 16:27:17.316199',1,1),
(455,'C',1,'2022-11-30 16:29:00.954633','2022-11-30 16:29:00.954639',1,1),
(456,'C',1,'2022-11-30 16:30:48.091615','2022-11-30 16:30:48.091622',1,1),
(457,'C',1,'2022-11-30 16:32:31.574850','2022-11-30 16:32:31.574855',1,1),
(458,'C',1,'2022-11-30 16:34:49.165006','2022-11-30 16:34:49.165011',1,1),
(459,'C',1,'2022-11-30 16:35:38.924118','2022-11-30 16:36:37.081776',1,0),
(460,'C',1,'2022-11-30 16:38:38.822492','2022-11-30 16:39:25.737306',1,0),
(461,'C',2,'2022-11-30 16:38:38.870106','2022-11-30 16:39:25.747199',1,0),
(462,'D',1,'2022-11-30 16:39:28.608093','2022-11-30 16:39:34.428328',1,0),
(463,'D',2,'2022-11-30 16:39:28.639004','2022-11-30 16:39:34.437153',1,0),
(464,'C',1,'2022-11-30 16:39:49.570400','2022-11-30 16:39:49.570407',1,1),
(465,'C',2,'2022-11-30 16:39:49.597396','2022-11-30 16:39:49.597404',1,1),
(466,'C',1,'2022-11-30 16:43:00.614570','2022-11-30 16:43:00.614577',1,1),
(467,'C',2,'2022-11-30 16:43:00.626998','2022-11-30 16:43:00.627003',1,1),
(468,'C',1,'2022-11-30 16:45:56.427087','2022-11-30 16:45:56.427092',1,1),
(469,'C',2,'2022-11-30 16:45:56.437437','2022-11-30 16:45:56.437441',1,1),
(470,'C',1,'2022-11-30 16:51:09.198173','2022-11-30 16:51:09.198180',1,1),
(471,'C',2,'2022-11-30 16:51:09.209547','2022-11-30 16:51:09.209556',1,1),
(472,'C',1,'2022-11-30 16:58:58.312707','2022-11-30 16:59:11.944254',1,0),
(473,'C',2,'2022-11-30 16:58:58.486147','2022-11-30 16:59:11.950948',1,0),
(474,'D',1,'2022-11-30 16:59:12.836039','2022-11-30 16:59:19.258503',1,0),
(475,'D',2,'2022-11-30 16:59:12.928928','2022-11-30 16:59:19.266879',1,0),
(476,'E',1,'2022-11-30 16:59:44.020774','2022-11-30 16:59:53.925477',1,0),
(477,'D',1,'2022-11-30 16:59:54.685389','2022-11-30 16:59:58.139174',1,0),
(478,'C',1,'2022-11-30 16:59:59.031984','2022-11-30 17:00:06.678944',1,0),
(479,'C',1,'2022-11-30 17:00:08.421769','2022-11-30 17:00:11.274964',1,0),
(480,'C',2,'2022-11-30 17:00:08.759978','2022-11-30 17:00:11.277994',1,0),
(481,'C',1,'2022-11-30 17:00:12.594261','2022-11-30 17:00:17.046083',1,0),
(482,'C',1,'2022-11-30 18:09:24.889654','2022-11-30 18:09:24.889659',1,1),
(483,'C',2,'2022-11-30 18:09:24.908086','2022-11-30 18:09:24.908093',1,1),
(484,'C',1,'2022-11-30 18:12:06.229650','2022-11-30 18:12:06.229746',1,1),
(485,'C',2,'2022-11-30 18:12:06.307844','2022-11-30 18:12:06.307850',1,1),
(486,'C',1,'2022-11-30 18:13:19.864696','2022-11-30 18:13:19.864701',1,1),
(487,'C',2,'2022-11-30 18:13:19.875659','2022-11-30 18:13:19.875668',1,1),
(488,'C',1,'2022-11-30 18:13:57.322846','2022-11-30 18:13:57.322853',1,1),
(489,'C',2,'2022-11-30 18:13:57.340342','2022-11-30 18:13:57.340349',1,1),
(490,'C',1,'2022-11-30 18:15:08.467003','2022-11-30 18:15:08.467007',1,1),
(491,'C',2,'2022-11-30 18:15:08.532458','2022-11-30 18:15:08.532463',1,1),
(492,'C',1,'2022-11-30 18:16:40.754195','2022-11-30 18:16:40.754202',1,1),
(493,'C',2,'2022-11-30 18:16:40.790499','2022-11-30 18:16:40.790507',1,1),
(494,'C',1,'2022-11-30 18:17:47.738502','2022-11-30 18:17:47.738508',1,1),
(495,'C',2,'2022-11-30 18:17:47.840084','2022-11-30 18:17:47.840091',1,1),
(496,'C',1,'2022-11-30 18:18:55.298161','2022-11-30 18:18:55.298185',1,1),
(497,'C',2,'2022-11-30 18:18:55.314252','2022-11-30 18:18:55.314276',1,1),
(498,'C',1,'2022-11-30 18:21:32.457787','2022-11-30 18:21:47.611008',1,0),
(499,'C',2,'2022-11-30 18:21:32.473934','2022-11-30 18:21:47.616709',1,0),
(500,'D',1,'2022-11-30 18:21:48.099158','2022-11-30 18:21:56.597197',1,0),
(501,'D',2,'2022-11-30 18:21:48.115248','2022-11-30 18:21:56.602978',1,0),
(502,'E',1,'2022-11-30 18:25:33.220716','2022-11-30 18:25:33.220725',1,1),
(503,'E',2,'2022-11-30 18:25:33.241186','2022-11-30 18:25:33.241197',1,1),
(504,'E',1,'2022-11-30 18:28:48.454594','2022-11-30 18:28:53.165161',1,0),
(505,'E',2,'2022-11-30 18:28:48.464396','2022-11-30 18:28:53.171739',1,0),
(506,'C',1,'2022-11-30 18:28:53.408803','2022-11-30 18:28:53.408808',1,1),
(507,'C',1,'2022-11-30 18:29:59.952956','2022-11-30 18:29:59.952963',1,1),
(508,'C',1,'2022-11-30 18:31:14.811467','2022-11-30 18:31:14.811473',1,1),
(509,'C',1,'2022-11-30 18:34:22.060967','2022-11-30 18:34:22.060973',1,1),
(510,'C',1,'2022-11-30 18:35:06.901283','2022-11-30 18:35:06.901290',1,1),
(511,'C',1,'2022-11-30 18:35:51.345331','2022-11-30 18:35:51.345335',1,1),
(512,'C',1,'2022-11-30 18:37:14.041123','2022-11-30 18:37:29.463127',1,0),
(513,'C',1,'2022-11-30 18:37:29.961825','2022-11-30 18:37:46.424556',1,0),
(514,'C',1,'2022-11-30 18:37:46.812868','2022-11-30 18:38:06.665197',1,0),
(515,'C',1,'2022-11-30 18:38:07.056847','2022-11-30 18:38:07.056852',1,1),
(516,'C',1,'2022-11-30 18:39:04.665355','2022-11-30 18:39:04.665360',1,1),
(517,'C',1,'2022-11-30 18:42:56.624820','2022-11-30 18:42:56.624826',1,1),
(518,'C',1,'2022-12-01 11:15:10.677798','2022-12-01 11:16:43.689410',1,0),
(519,'C',2,'2022-12-01 11:15:10.698147','2022-12-01 11:16:43.695169',1,0),
(520,'C',1,'2022-12-01 11:24:14.360440','2022-12-01 11:24:22.280991',1,0),
(521,'C',2,'2022-12-01 11:24:14.375166','2022-12-01 11:24:22.288932',1,0),
(522,'C',1,'2022-12-01 11:30:29.850404','2022-12-01 11:30:34.492498',1,0),
(523,'C',2,'2022-12-01 11:30:29.866423','2022-12-01 11:30:34.500944',1,0),
(524,'C',1,'2022-12-01 11:31:28.927112','2022-12-01 11:31:35.014623',1,0),
(525,'C',2,'2022-12-01 11:31:28.997148','2022-12-01 11:31:35.020796',1,0),
(526,'C',1,'2022-12-01 12:47:35.346309','2022-12-01 12:47:37.653727',1,0),
(527,'C',2,'2022-12-01 12:47:35.361601','2022-12-01 12:47:37.665152',1,0),
(528,'C',1,'2022-12-01 14:05:47.103993','2022-12-01 14:05:49.419110',1,0),
(529,'C',2,'2022-12-01 14:05:47.164806','2022-12-01 14:05:49.425455',1,0),
(530,'C',1,'2022-12-02 14:37:01.155814','2022-12-02 14:37:10.686503',1,0),
(531,'C',2,'2022-12-02 14:37:01.166226','2022-12-02 14:37:10.691191',1,0),
(532,'E',1,'2022-12-02 14:37:11.366041','2022-12-02 14:37:11.366048',1,1),
(533,'E',1,'2022-12-02 14:38:15.093856','2022-12-02 14:38:37.761943',1,0),
(534,'C',1,'2022-12-02 14:54:27.942071','2022-12-02 14:54:30.709502',1,0),
(535,'C',2,'2022-12-02 14:54:27.963987','2022-12-02 14:54:30.716297',1,0),
(536,'C',1,'2022-12-03 22:54:45.026089','2022-12-03 22:55:26.681466',1,0),
(537,'C',2,'2022-12-03 22:54:45.056921','2022-12-03 22:55:26.689701',1,0),
(538,'C',1,'2022-12-03 22:55:27.218581','2022-12-03 22:55:35.494004',1,0),
(539,'C',1,'2022-12-07 15:51:18.476867','2022-12-07 15:51:18.476871',1,1),
(540,'C',2,'2022-12-07 15:51:18.527302','2022-12-07 15:51:18.527308',1,1),
(541,'C',1,'2022-12-07 15:52:24.354123','2022-12-07 15:52:24.354129',1,1),
(542,'C',2,'2022-12-07 15:52:24.389038','2022-12-07 15:52:24.389046',1,1),
(543,'C',1,'2022-12-07 15:54:07.422915','2022-12-07 15:54:07.422921',1,1),
(544,'C',2,'2022-12-07 15:54:07.513489','2022-12-07 15:54:07.513495',1,1),
(545,'C',1,'2022-12-07 17:42:55.998862','2022-12-07 17:43:03.902658',1,0),
(546,'C',2,'2022-12-07 17:42:56.073180','2022-12-07 17:43:03.908644',1,0),
(547,'C',1,'2022-12-07 17:43:04.717600','2022-12-07 17:43:14.267870',1,0),
(548,'E',1,'2022-12-07 17:43:15.230120','2022-12-07 17:43:24.076233',1,0),
(549,'C',1,'2022-12-07 17:43:29.397708','2022-12-07 17:43:31.197554',1,0),
(550,'C',2,'2022-12-07 17:43:29.415179','2022-12-07 17:43:31.201175',1,0),
(551,'C',1,'2022-12-07 17:43:38.903538','2022-12-07 17:43:41.943125',1,0),
(552,'C',2,'2022-12-07 17:43:38.917191','2022-12-07 17:43:41.949564',1,0),
(553,'C',1,'2022-12-07 17:44:40.160840','2022-12-07 17:44:42.624462',1,0),
(554,'C',2,'2022-12-07 17:44:40.194933','2022-12-07 17:44:42.628282',1,0),
(555,'C',1,'2022-12-07 17:55:05.363059','2022-12-07 17:55:07.355375',1,0),
(556,'C',2,'2022-12-07 17:55:05.396900','2022-12-07 17:55:07.362188',1,0),
(557,'C',1,'2022-12-07 17:56:56.799952','2022-12-07 17:57:00.501667',1,0),
(558,'C',2,'2022-12-07 17:56:56.853134','2022-12-07 17:57:00.505646',1,0),
(559,'C',1,'2022-12-07 18:09:07.944936','2022-12-07 18:09:10.364576',1,0),
(560,'C',2,'2022-12-07 18:09:07.985878','2022-12-07 18:09:10.368708',1,0),
(561,'C',1,'2022-12-07 18:09:47.218887','2022-12-07 18:09:49.572176',1,0),
(562,'C',2,'2022-12-07 18:09:47.248080','2022-12-07 18:09:49.576104',1,0),
(563,'C',1,'2022-12-07 18:11:42.778580','2022-12-07 18:11:44.910211',1,0),
(564,'C',2,'2022-12-07 18:11:42.839975','2022-12-07 18:11:44.916018',1,0),
(565,'C',1,'2022-12-07 18:12:09.114285','2022-12-07 18:12:11.066615',1,0),
(566,'C',2,'2022-12-07 18:12:09.218668','2022-12-07 18:12:11.071992',1,0),
(567,'C',1,'2022-12-07 19:29:55.176112','2022-12-07 19:29:57.558223',1,0),
(568,'C',2,'2022-12-07 19:29:55.197866','2022-12-07 19:29:57.564714',1,0),
(569,'C',1,'2022-12-07 19:30:20.481340','2022-12-07 19:30:24.874158',1,0),
(570,'C',2,'2022-12-07 19:30:20.516698','2022-12-07 19:30:24.881746',1,0),
(571,'C',1,'2022-12-07 19:31:42.440960','2022-12-07 19:31:44.485816',1,0),
(572,'C',2,'2022-12-07 19:31:42.463681','2022-12-07 19:31:44.490656',1,0),
(573,'C',1,'2022-12-07 19:44:02.252825','2022-12-07 19:44:07.353654',1,0),
(574,'C',2,'2022-12-07 19:44:02.293712','2022-12-07 19:44:07.361499',1,0),
(575,'C',1,'2022-12-07 19:47:36.617385','2022-12-07 19:47:38.704186',1,0),
(576,'C',2,'2022-12-07 19:47:36.648831','2022-12-07 19:47:38.715159',1,0),
(577,'C',1,'2022-12-07 19:48:30.708555','2022-12-07 19:48:32.349691',1,0),
(578,'C',2,'2022-12-07 19:48:30.728728','2022-12-07 19:48:32.356417',1,0),
(579,'C',1,'2022-12-08 20:38:52.534882','2022-12-08 20:38:54.735358',1,0),
(580,'C',2,'2022-12-08 20:38:52.545719','2022-12-08 20:38:54.741374',1,0),
(581,'C',1,'2022-12-09 17:05:05.914743','2022-12-09 17:06:04.994139',1,0),
(582,'C',2,'2022-12-09 17:05:05.946412','2022-12-09 17:06:04.997598',1,0),
(583,'C',1,'2022-12-09 17:06:05.694188','2022-12-09 17:06:29.038768',1,0),
(584,'C',1,'2022-12-09 17:06:30.476422','2022-12-09 17:06:30.476431',1,1),
(585,'C',1,'2022-12-09 17:09:28.299515','2022-12-09 17:09:28.299521',1,1),
(586,'C',1,'2022-12-09 17:10:50.027705','2022-12-09 17:10:50.027714',1,1),
(587,'C',1,'2022-12-09 17:16:29.695311','2022-12-09 17:16:29.695317',1,1),
(588,'C',1,'2022-12-09 17:18:47.376484','2022-12-09 17:18:58.416420',1,0),
(589,'D',1,'2022-12-09 17:18:59.138963','2022-12-09 17:19:03.560055',1,0),
(590,'E',1,'2022-12-09 17:19:04.319322','2022-12-09 17:19:04.319328',1,1),
(591,'C',1,'2022-12-11 11:19:38.748470','2022-12-11 11:19:49.891228',1,0),
(592,'C',2,'2022-12-11 11:19:38.774413','2022-12-11 11:19:49.909316',1,0),
(593,'C',1,'2022-12-11 11:20:09.124113','2022-12-11 11:20:09.124120',1,1),
(594,'C',2,'2022-12-11 11:20:09.133532','2022-12-11 11:20:09.133539',1,1),
(595,'C',1,'2022-12-11 11:24:46.196077','2022-12-11 11:24:52.907096',1,0),
(596,'C',1,'2022-12-11 11:24:53.424385','2022-12-11 11:25:36.215542',1,0),
(597,'C',1,'2022-12-11 11:25:39.519858','2022-12-11 11:25:51.925158',1,0),
(598,'E',1,'2022-12-11 11:25:52.302342','2022-12-11 11:27:00.593194',1,0),
(599,'C',1,'2022-12-11 11:27:05.434488','2022-12-11 11:27:09.673240',1,0),
(600,'E',1,'2022-12-11 11:27:09.986350','2022-12-11 11:29:20.116507',1,0),
(601,'C',1,'2022-12-11 11:29:28.242857','2022-12-11 11:29:33.122505',1,0),
(602,'E',1,'2022-12-11 11:29:33.471736','2022-12-11 11:29:45.323116',1,0),
(603,'C',1,'2022-12-11 11:30:14.174316','2022-12-11 11:30:18.900690',1,0),
(604,'E',1,'2022-12-11 11:30:19.218731','2022-12-11 11:30:44.593405',1,0),
(605,'C',1,'2022-12-11 11:30:48.020637','2022-12-11 11:30:58.024451',1,0),
(606,'C',1,'2022-12-11 11:31:06.450616','2022-12-11 11:31:12.666810',1,0),
(607,'C',1,'2022-12-11 11:31:28.881537','2022-12-11 11:31:37.308836',1,0),
(608,'C',1,'2022-12-11 11:32:38.918013','2022-12-11 11:32:56.270178',1,0),
(609,'E',1,'2022-12-11 11:32:56.676889','2022-12-11 11:34:25.315233',1,0),
(610,'C',1,'2022-12-11 11:59:03.899856','2022-12-11 11:59:10.599542',1,0),
(611,'C',1,'2022-12-11 11:59:15.381622','2022-12-11 11:59:19.513719',1,0),
(612,'E',1,'2022-12-11 11:59:19.859997','2022-12-11 11:59:19.860002',1,1),
(613,'E',1,'2022-12-11 12:02:45.611018','2022-12-11 12:03:05.618259',1,0),
(614,'C',1,'2022-12-11 12:06:39.913810','2022-12-11 12:06:43.168065',1,0),
(615,'E',1,'2022-12-11 12:06:43.822572','2022-12-11 12:07:06.641390',1,0),
(616,'E',1,'2022-12-11 12:07:07.059087','2022-12-11 12:09:20.617582',1,0),
(617,'C',1,'2022-12-11 12:10:03.920317','2022-12-11 12:10:25.494922',1,0),
(618,'C',1,'2022-12-11 12:10:25.759754','2022-12-11 12:10:55.160455',1,0),
(619,'C',1,'2022-12-11 12:10:55.581998','2022-12-11 12:11:39.051899',1,0),
(620,'E',1,'2022-12-11 12:11:40.594011','2022-12-11 12:11:53.890688',1,0),
(621,'C',1,'2022-12-11 12:11:54.489650','2022-12-11 12:13:17.247353',1,0),
(622,'C',1,'2022-12-11 12:13:17.743866','2022-12-11 12:13:17.743876',1,1),
(623,'C',1,'2022-12-11 12:20:58.502925','2022-12-11 12:21:17.736856',1,0),
(624,'E',1,'2022-12-11 12:21:18.081638','2022-12-11 12:21:20.120498',1,0),
(625,'E',1,'2022-12-11 12:21:20.384527','2022-12-11 12:21:20.384534',1,1),
(626,'E',1,'2022-12-11 12:35:24.642400','2022-12-11 12:35:24.642405',1,1),
(627,'E',1,'2022-12-11 12:38:35.338967','2022-12-11 12:42:31.592612',1,0),
(628,'C',1,'2022-12-12 13:38:32.335821','2022-12-12 13:38:35.313980',1,0),
(629,'C',1,'2022-12-12 16:01:39.713876','2022-12-12 16:01:42.503136',1,0),
(630,'C',1,'2022-12-12 18:05:43.069542','2022-12-12 18:05:53.764768',1,0),
(631,'E',1,'2022-12-12 18:05:54.238069','2022-12-12 18:06:18.237885',1,0),
(632,'E',1,'2022-12-12 18:06:18.557087','2022-12-12 18:07:09.661159',1,0),
(633,'E',1,'2022-12-12 18:07:27.247985','2022-12-12 18:07:27.247989',1,1),
(634,'E',1,'2022-12-12 18:28:10.892102','2022-12-12 18:28:10.892109',1,1),
(635,'E',1,'2022-12-12 18:32:38.572316','2022-12-12 18:32:38.572325',1,1),
(636,'E',1,'2022-12-12 18:36:19.058010','2022-12-12 18:36:19.058014',1,1),
(637,'E',1,'2022-12-12 18:44:11.877688','2022-12-12 18:44:11.877698',1,1),
(638,'E',1,'2022-12-12 18:50:24.057170','2022-12-12 18:50:24.057174',1,1),
(639,'E',1,'2022-12-12 18:52:13.658963','2022-12-12 18:52:13.658967',1,1),
(640,'E',1,'2022-12-12 18:56:14.837724','2022-12-12 18:56:14.837729',1,1),
(641,'E',1,'2022-12-12 19:17:08.093944','2022-12-12 19:17:08.093950',1,1),
(642,'E',1,'2022-12-12 19:27:22.985867','2022-12-12 19:27:22.985873',1,1),
(643,'E',1,'2022-12-12 19:31:44.933353','2022-12-12 19:31:44.933360',1,1),
(644,'E',1,'2022-12-12 19:37:48.336029','2022-12-12 19:37:48.336033',1,1),
(645,'E',1,'2022-12-12 19:50:33.684770','2022-12-12 19:50:33.684776',1,1),
(646,'E',1,'2022-12-12 19:55:27.599612','2022-12-12 19:55:27.599619',1,1),
(647,'E',1,'2022-12-12 20:08:20.190639','2022-12-12 20:08:20.190649',1,1),
(648,'C',1,'2022-12-14 13:05:10.644358','2022-12-14 13:05:10.644362',1,1),
(649,'E',1,'2022-12-14 13:27:53.428161','2022-12-14 13:28:03.577793',1,0),
(650,'E',1,'2022-12-14 13:28:05.658277','2022-12-14 13:28:05.658281',1,1),
(651,'C',1,'2022-12-15 12:27:50.645181','2022-12-15 12:28:00.038578',1,0),
(652,'E',1,'2022-12-15 12:28:00.437340','2022-12-15 12:28:00.437345',1,1),
(653,'E',1,'2022-12-15 12:29:35.728800','2022-12-15 12:29:35.728804',1,1),
(654,'E',1,'2022-12-15 12:40:16.440503','2022-12-15 12:40:16.440509',1,1),
(655,'E',1,'2022-12-15 12:52:43.348503','2022-12-15 12:52:43.348507',1,1),
(656,'C',1,'2022-12-16 10:23:27.731689','2022-12-16 10:23:37.844215',1,0),
(657,'E',1,'2022-12-16 10:23:38.268629','2022-12-16 10:23:38.268634',1,1),
(658,'E',1,'2022-12-16 10:32:24.621231','2022-12-16 10:32:24.621236',1,1),
(659,'E',1,'2022-12-16 10:36:42.206295','2022-12-16 10:36:42.206300',1,1),
(660,'E',1,'2022-12-16 10:38:14.370672','2022-12-16 10:38:14.370677',1,1),
(661,'E',1,'2022-12-16 10:41:30.777595','2022-12-16 10:41:30.777603',1,1),
(662,'E',1,'2022-12-16 10:43:57.468578','2022-12-16 10:43:57.468583',1,1),
(663,'E',1,'2022-12-16 12:24:38.035145','2022-12-16 12:24:38.035149',1,1),
(664,'E',1,'2022-12-16 12:26:06.100355','2022-12-16 12:26:06.100361',1,1),
(665,'E',1,'2022-12-16 12:45:24.659089','2022-12-16 12:45:24.659094',1,1),
(666,'E',1,'2022-12-16 12:48:52.877639','2022-12-16 12:48:52.877644',1,1),
(667,'E',1,'2022-12-16 12:55:59.896942','2022-12-16 12:55:59.896946',1,1),
(668,'E',1,'2022-12-16 12:59:00.251709','2022-12-16 12:59:00.251713',1,1),
(669,'E',1,'2022-12-16 13:06:09.295580','2022-12-16 13:06:09.295584',1,1),
(670,'E',1,'2022-12-16 13:10:02.711331','2022-12-16 13:10:02.711336',1,1),
(671,'E',1,'2022-12-16 13:12:18.903873','2022-12-16 13:12:18.903878',1,1),
(672,'E',1,'2022-12-16 13:21:47.625292','2022-12-16 13:21:47.625296',1,1),
(673,'E',1,'2022-12-16 13:22:39.822549','2022-12-16 13:22:39.822554',1,1),
(674,'E',1,'2022-12-16 13:25:40.770418','2022-12-16 13:25:40.770424',1,1),
(675,'E',1,'2022-12-16 13:26:26.961088','2022-12-16 13:26:26.961093',1,1),
(676,'E',1,'2022-12-16 13:28:14.311288','2022-12-16 13:28:14.311296',1,1),
(677,'E',1,'2022-12-16 13:37:22.164294','2022-12-16 13:38:05.165270',1,0),
(678,'C',1,'2022-12-16 13:38:05.470892','2022-12-16 13:39:09.667218',1,0),
(679,'C',1,'2022-12-16 13:39:10.111683','2022-12-16 13:39:25.248446',1,0),
(680,'E',1,'2022-12-16 13:39:25.640057','2022-12-16 13:39:25.640063',1,1),
(681,'E',1,'2022-12-16 13:40:33.234716','2022-12-16 13:40:33.234725',1,1),
(682,'E',1,'2022-12-16 13:41:33.396284','2022-12-16 13:41:33.396289',1,1),
(683,'E',1,'2022-12-16 13:42:56.988575','2022-12-16 13:42:56.988579',1,1),
(684,'C',1,'2022-12-16 14:29:58.404139','2022-12-16 14:30:04.719488',1,0),
(685,'C',1,'2022-12-16 14:49:42.615111','2022-12-16 14:49:44.731853',1,0),
(686,'C',1,'2022-12-16 16:04:31.800589','2022-12-16 16:05:23.013744',1,0),
(687,'C',1,'2022-12-16 16:05:23.461476','2022-12-16 16:05:23.461482',1,1),
(688,'C',1,'2022-12-16 16:10:19.900504','2022-12-16 16:10:19.900512',1,1),
(689,'C',1,'2022-12-16 16:14:00.429851','2022-12-16 16:14:00.429856',1,1),
(690,'C',1,'2022-12-16 16:17:33.507170','2022-12-16 16:17:33.507178',1,1),
(691,'C',1,'2022-12-16 16:25:21.806900','2022-12-16 16:25:21.806907',1,1),
(692,'C',1,'2022-12-16 16:26:42.842568','2022-12-16 16:26:42.842575',1,1),
(693,'C',1,'2022-12-16 16:32:17.617550','2022-12-16 16:32:17.617556',1,1),
(694,'C',1,'2022-12-16 16:35:09.154557','2022-12-16 16:35:09.154562',1,1),
(695,'C',1,'2022-12-16 16:41:52.467926','2022-12-16 16:49:44.750410',1,0),
(696,'C',1,'2022-12-16 16:49:46.565152','2022-12-16 16:49:46.565158',1,1),
(697,'C',1,'2022-12-16 16:50:13.183769','2022-12-16 16:50:13.183776',1,1),
(698,'C',1,'2022-12-16 16:52:40.337795','2022-12-16 16:52:40.337799',1,1),
(699,'C',1,'2022-12-16 16:53:18.718947','2022-12-16 16:55:45.173935',1,0),
(700,'C',1,'2022-12-16 16:55:46.375314','2022-12-16 16:55:50.315436',1,0),
(701,'C',1,'2022-12-16 16:55:50.490659','2022-12-16 16:56:03.470227',1,0),
(702,'C',1,'2022-12-16 16:56:03.643319','2022-12-16 16:56:05.588832',1,0),
(703,'C',1,'2022-12-16 16:56:05.779612','2022-12-16 16:56:05.779621',1,1),
(704,'C',1,'2022-12-16 16:56:48.576422','2022-12-16 16:56:48.576427',1,1),
(705,'C',1,'2022-12-16 16:59:58.130197','2022-12-16 16:59:58.130204',1,1),
(706,'C',1,'2022-12-16 17:04:46.018536','2022-12-16 17:04:46.018542',1,1),
(707,'C',1,'2022-12-16 17:06:31.831483','2022-12-16 17:06:31.831489',1,1),
(708,'C',1,'2022-12-16 17:08:04.724409','2022-12-16 17:08:04.724413',1,1),
(709,'C',1,'2022-12-16 17:08:57.200419','2022-12-16 17:08:57.200433',1,1),
(710,'C',1,'2022-12-16 17:09:27.036088','2022-12-16 17:09:27.036095',1,1),
(711,'C',1,'2022-12-16 17:11:03.397532','2022-12-16 17:11:03.397539',1,1),
(712,'C',1,'2022-12-16 17:12:48.850879','2022-12-16 17:12:48.850884',1,1),
(713,'C',1,'2022-12-16 17:17:24.406021','2022-12-16 17:17:28.769535',1,0),
(714,'C',1,'2022-12-16 17:38:29.805084','2022-12-16 17:38:34.697070',1,0),
(715,'C',1,'2022-12-16 17:38:35.837504','2022-12-16 17:38:35.837512',1,1),
(716,'C',1,'2022-12-16 17:44:58.485443','2022-12-16 17:44:58.485450',1,1),
(717,'C',1,'2022-12-16 17:47:39.730415','2022-12-16 17:47:39.730423',1,1),
(718,'C',1,'2022-12-16 17:51:11.010865','2022-12-16 17:51:11.010870',1,1),
(719,'C',1,'2022-12-16 17:52:02.118090','2022-12-16 17:52:48.472214',1,0),
(720,'C',1,'2022-12-16 17:52:49.691695','2022-12-16 17:52:49.691702',1,1),
(721,'C',1,'2022-12-16 17:55:44.647166','2022-12-16 17:55:44.647173',1,1),
(722,'C',1,'2022-12-16 17:56:11.574344','2022-12-16 17:56:11.574351',1,1),
(723,'C',1,'2022-12-16 17:56:29.991833','2022-12-16 17:56:29.991838',1,1),
(724,'C',1,'2022-12-16 17:56:57.817009','2022-12-16 17:56:57.817017',1,1),
(725,'C',1,'2022-12-16 17:58:07.963500','2022-12-16 17:58:07.963506',1,1),
(726,'C',1,'2022-12-16 18:09:19.422335','2022-12-16 18:09:19.422341',1,1),
(727,'C',1,'2022-12-16 18:09:42.919448','2022-12-16 18:09:42.919456',1,1),
(728,'C',1,'2022-12-16 18:13:40.172864','2022-12-16 18:13:40.172870',1,1),
(729,'C',1,'2022-12-16 18:14:31.835353','2022-12-16 18:14:31.835358',1,1),
(730,'C',1,'2022-12-16 18:16:43.909498','2022-12-16 18:16:43.909503',1,1),
(731,'C',1,'2022-12-16 18:17:27.267075','2022-12-16 18:17:27.267082',1,1),
(732,'C',1,'2022-12-16 18:21:04.842285','2022-12-16 18:21:04.842291',1,1),
(733,'C',1,'2022-12-16 18:22:07.513111','2022-12-16 18:22:07.513117',1,1),
(734,'C',1,'2022-12-16 18:34:02.876206','2022-12-16 18:35:01.650972',1,0),
(735,'C',1,'2022-12-16 18:45:32.715482','2022-12-16 18:45:33.256102',1,0),
(736,'C',1,'2022-12-16 18:45:34.156237','2022-12-16 18:45:34.156243',1,1),
(737,'C',1,'2022-12-16 18:54:04.936580','2022-12-16 18:54:04.936586',1,1),
(738,'C',1,'2022-12-16 18:57:52.242971','2022-12-16 18:57:52.242975',1,1),
(739,'C',1,'2022-12-16 18:59:01.523875','2022-12-16 18:59:01.523879',1,1),
(740,'C',1,'2022-12-17 09:54:15.738396','2022-12-17 09:54:15.738403',1,1),
(741,'C',1,'2022-12-17 09:56:52.538589','2022-12-17 09:56:52.538595',1,1),
(742,'C',1,'2022-12-17 09:57:48.310099','2022-12-17 09:57:48.310104',1,1),
(743,'C',1,'2022-12-17 10:05:32.060660','2022-12-17 10:05:32.060664',1,1),
(744,'C',1,'2022-12-17 10:06:32.462550','2022-12-17 10:06:32.462555',1,1),
(745,'C',1,'2022-12-17 10:09:04.481156','2022-12-17 10:09:04.481162',1,1),
(746,'C',1,'2022-12-17 10:11:47.481382','2022-12-17 10:11:47.481389',1,1),
(747,'C',1,'2022-12-17 10:13:13.727365','2022-12-17 10:13:13.727371',1,1),
(748,'C',1,'2022-12-17 10:17:06.004431','2022-12-17 10:17:06.004438',1,1),
(749,'C',1,'2022-12-17 10:17:33.081669','2022-12-17 10:17:33.081675',1,1),
(750,'C',1,'2022-12-17 10:18:42.334908','2022-12-17 10:18:42.334920',1,1),
(751,'C',1,'2022-12-17 10:19:25.915313','2022-12-17 10:19:25.915319',1,1),
(752,'C',1,'2022-12-17 10:19:58.359282','2022-12-17 10:19:58.359288',1,1),
(753,'C',1,'2022-12-17 10:20:42.791486','2022-12-17 10:20:42.791493',1,1),
(754,'C',1,'2022-12-17 10:21:00.128407','2022-12-17 10:21:00.128413',1,1),
(755,'C',1,'2022-12-17 10:21:48.768624','2022-12-17 10:21:48.768633',1,1),
(756,'C',1,'2022-12-17 10:22:36.966685','2022-12-17 10:22:36.966693',1,1),
(757,'C',1,'2022-12-17 10:31:30.370578','2022-12-17 10:32:21.837012',1,0),
(758,'C',1,'2022-12-17 10:32:22.473549','2022-12-17 10:32:22.473557',1,1),
(759,'C',1,'2022-12-17 10:34:47.216718','2022-12-17 10:34:47.216724',1,1),
(760,'C',1,'2022-12-17 10:36:02.852929','2022-12-17 10:36:02.852941',1,1),
(761,'C',1,'2022-12-17 10:43:42.198611','2022-12-17 10:43:42.198617',1,1),
(762,'C',1,'2022-12-17 10:45:32.537878','2022-12-17 10:45:32.537887',1,1),
(763,'C',1,'2022-12-17 10:46:58.523702','2022-12-17 10:46:58.523709',1,1),
(764,'C',1,'2022-12-17 10:51:31.584212','2022-12-17 10:51:31.584219',1,1),
(765,'C',1,'2022-12-17 10:53:20.615159','2022-12-17 10:53:20.615167',1,1),
(766,'C',1,'2022-12-17 11:01:16.038720','2022-12-17 11:01:16.038726',1,1),
(767,'C',1,'2022-12-17 11:03:01.914749','2022-12-17 11:03:01.914756',1,1),
(768,'C',1,'2022-12-17 11:03:56.107236','2022-12-17 11:03:56.107244',1,1),
(769,'C',1,'2022-12-17 11:09:40.738707','2022-12-17 11:09:40.738714',1,1),
(770,'C',1,'2022-12-17 11:30:42.061498','2022-12-17 11:30:42.061504',1,1),
(771,'C',1,'2022-12-17 12:24:09.281326','2022-12-17 12:25:29.821860',1,0),
(772,'C',1,'2022-12-17 12:25:51.518765','2022-12-17 12:26:05.058674',1,0),
(773,'C',1,'2022-12-17 12:26:12.979643','2022-12-17 12:26:16.856025',1,0),
(774,'E',1,'2022-12-17 12:26:17.396790','2022-12-17 12:27:03.596289',1,0),
(775,'C',1,'2022-12-17 12:27:06.918893','2022-12-17 12:27:54.017450',1,0),
(776,'C',1,'2022-12-17 12:28:00.384742','2022-12-17 12:28:02.463074',1,0),
(777,'E',1,'2022-12-17 12:28:03.173546','2022-12-17 12:28:30.253598',1,0),
(778,'C',1,'2022-12-17 12:28:56.693302','2022-12-17 12:28:56.693309',1,1),
(779,'E',1,'2022-12-17 12:31:40.518782','2022-12-17 12:32:01.331853',1,0),
(780,'C',1,'2022-12-17 12:32:34.274666','2022-12-17 12:32:37.205373',1,0),
(781,'C',1,'2022-12-17 12:33:33.599262','2022-12-17 12:33:36.287658',1,0),
(782,'E',1,'2022-12-17 12:33:36.889084','2022-12-17 12:36:04.498047',1,0),
(783,'E',1,'2022-12-17 12:36:05.638748','2022-12-17 12:36:05.638766',1,1),
(784,'C',1,'2022-12-17 12:45:14.600177','2022-12-17 12:45:18.440882',1,0),
(785,'E',1,'2022-12-17 12:45:18.790043','2022-12-17 12:46:20.482748',1,0),
(786,'C',1,'2022-12-17 12:47:42.798759','2022-12-17 12:47:46.658446',1,0),
(787,'E',1,'2022-12-17 12:47:47.211227','2022-12-17 12:47:53.511467',1,0),
(788,'C',1,'2022-12-17 12:47:59.526029','2022-12-17 12:48:06.775125',1,0),
(789,'E',1,'2022-12-17 12:48:07.695200','2022-12-17 12:48:12.904187',1,0),
(790,'C',1,'2022-12-17 12:48:19.187275','2022-12-17 12:48:51.309078',1,0),
(791,'C',1,'2022-12-17 12:49:18.714717','2022-12-17 12:49:23.120661',1,0),
(792,'C',1,'2022-12-17 12:49:30.732846','2022-12-17 12:49:38.820881',1,0),
(793,'C',1,'2022-12-17 12:49:59.504477','2022-12-17 12:50:01.977516',1,0),
(794,'E',1,'2022-12-17 12:50:02.597936','2022-12-17 12:50:24.391536',1,0),
(795,'C',1,'2022-12-18 12:35:50.008541','2022-12-18 12:35:54.649512',1,0),
(796,'C',1,'2022-12-18 21:06:16.839391','2022-12-18 21:06:16.839396',1,1),
(797,'C',1,'2022-12-20 11:45:51.528888','2022-12-20 11:45:59.486057',1,0),
(798,'C',1,'2022-12-20 12:17:44.926411','2022-12-20 12:17:50.676672',1,0),
(799,'E',1,'2022-12-20 12:17:51.339363','2022-12-20 12:20:37.970374',1,0),
(800,'C',1,'2022-12-20 12:20:50.359215','2022-12-20 12:21:33.624622',1,0),
(801,'C',1,'2022-12-20 14:12:33.232435','2022-12-20 14:12:38.701329',1,0),
(802,'E',1,'2022-12-20 14:12:38.980491','2022-12-20 14:12:38.980495',1,1),
(803,'C',1,'2022-12-20 18:57:28.147737','2022-12-20 18:57:31.772684',1,0),
(804,'C',1,'2022-12-20 20:58:22.015319','2022-12-20 20:58:26.841076',1,0),
(805,'C',1,'2022-12-20 20:58:27.278811','2022-12-20 20:58:41.113445',1,0),
(806,'C',1,'2022-12-21 10:42:08.431859','2022-12-21 10:42:12.318496',1,0),
(807,'E',1,'2022-12-21 10:42:12.774014','2022-12-21 10:42:12.774019',1,1),
(808,'E',1,'2022-12-21 10:46:04.210254','2022-12-21 10:46:04.210260',1,1),
(809,'E',1,'2022-12-21 10:47:04.108674','2022-12-21 10:47:04.108681',1,1),
(810,'E',1,'2022-12-21 10:49:55.162975','2022-12-21 10:49:55.162981',1,1),
(811,'E',1,'2022-12-21 10:51:02.995914','2022-12-21 10:51:02.995918',1,1),
(812,'C',1,'2022-12-25 11:08:41.737157','2022-12-25 11:08:54.349359',1,0),
(813,'E',1,'2022-12-25 11:08:54.875868','2022-12-25 11:08:54.875872',1,1),
(814,'E',1,'2022-12-25 11:13:22.798572','2022-12-25 11:13:26.098914',1,0),
(815,'E',1,'2022-12-25 11:13:26.536480','2022-12-25 11:13:51.578296',1,0),
(816,'C',1,'2022-12-25 11:13:52.294059','2022-12-25 11:14:07.749428',1,0),
(817,'C',1,'2022-12-25 11:14:08.164502','2022-12-25 11:15:03.629971',1,0),
(818,'E',1,'2022-12-25 11:15:04.188550','2022-12-25 11:15:04.188555',1,1),
(819,'E',1,'2022-12-25 11:22:28.170781','2022-12-25 11:22:28.170791',1,1),
(820,'E',1,'2022-12-25 11:24:30.628947','2022-12-25 11:24:30.628955',1,1),
(821,'E',1,'2022-12-25 11:26:40.754248','2022-12-25 11:26:40.754255',1,1),
(822,'E',1,'2022-12-25 11:48:40.596101','2022-12-25 11:48:40.596109',1,1),
(823,'E',1,'2022-12-25 11:51:37.674699','2022-12-25 11:51:37.674705',1,1),
(824,'E',1,'2022-12-25 11:52:49.883100','2022-12-25 11:52:49.883106',1,1),
(825,'E',1,'2022-12-25 11:56:02.347070','2022-12-25 11:56:02.347080',1,1),
(826,'E',1,'2022-12-25 11:59:16.047639','2022-12-25 11:59:16.047645',1,1),
(827,'E',1,'2022-12-25 12:05:39.079614','2022-12-25 12:05:39.079618',1,1),
(828,'E',1,'2022-12-25 12:12:47.501481','2022-12-25 12:12:47.501487',1,1),
(829,'E',1,'2022-12-25 12:24:47.032376','2022-12-25 12:24:47.032382',1,1),
(830,'C',1,'2022-12-26 11:55:02.229047','2022-12-26 11:55:10.047929',1,0),
(831,'E',1,'2022-12-26 11:55:10.838095','2022-12-26 11:55:10.838102',1,1),
(832,'C',1,'2022-12-26 12:07:25.476606','2022-12-26 12:14:09.604128',1,0),
(833,'C',1,'2022-12-26 13:29:50.290386','2022-12-26 13:29:55.688840',1,0),
(834,'E',1,'2022-12-26 13:29:56.105388','2022-12-26 13:30:25.380532',1,0),
(835,'C',1,'2022-12-26 15:57:10.987343','2022-12-26 15:57:10.987351',1,1),
(836,'C',1,'2022-12-26 18:37:33.647446','2022-12-26 18:37:36.497705',1,0),
(837,'E',1,'2022-12-26 18:37:38.251623','2022-12-26 18:37:38.251636',1,1),
(838,'E',1,'2022-12-26 18:42:46.558655','2022-12-26 18:42:46.558665',1,1),
(839,'E',1,'2022-12-26 18:50:13.086003','2022-12-26 18:50:13.086012',1,1),
(840,'E',1,'2022-12-26 19:20:57.751483','2022-12-26 19:20:57.751490',1,1),
(841,'E',1,'2022-12-26 19:40:30.270979','2022-12-26 19:40:30.270984',1,1),
(842,'E',1,'2022-12-26 19:51:03.329388','2022-12-26 19:51:03.329395',1,1),
(843,'E',1,'2022-12-26 20:00:25.896224','2022-12-26 20:00:25.896231',1,1),
(844,'E',1,'2022-12-26 20:10:04.606926','2022-12-26 20:10:04.606931',1,1),
(845,'E',1,'2022-12-26 20:28:15.139988','2022-12-26 20:28:15.139997',1,1),
(846,'E',1,'2022-12-26 20:36:38.445570','2022-12-26 20:36:44.215771',1,0),
(847,'C',1,'2022-12-26 20:37:30.912501','2022-12-26 20:37:33.569828',1,0),
(848,'C',1,'2022-12-26 20:38:12.575815','2022-12-26 20:38:15.223733',1,0),
(849,'C',1,'2022-12-27 09:26:05.454002','2022-12-27 09:26:25.449884',1,0),
(850,'C',1,'2022-12-27 09:26:25.994453','2022-12-27 09:26:25.994462',1,1),
(851,'E',1,'2022-12-27 10:03:26.830075','2022-12-27 10:03:26.830081',1,1),
(852,'C',1,'2022-12-27 11:42:32.827979','2022-12-27 11:42:35.396710',1,0),
(853,'E',1,'2022-12-27 11:42:36.472019','2022-12-27 11:42:36.472041',1,1),
(854,'C',1,'2022-12-27 11:58:05.796962','2022-12-27 11:58:09.235685',1,0),
(855,'E',1,'2022-12-27 11:58:10.262418','2022-12-27 11:58:10.262426',1,1),
(856,'E',1,'2022-12-27 12:07:42.038079','2022-12-27 12:07:42.038084',1,1),
(857,'E',1,'2022-12-27 13:19:16.355191','2022-12-27 13:19:53.989703',1,0),
(858,'C',1,'2022-12-27 13:26:01.865171','2022-12-27 13:26:03.788607',1,0),
(859,'C',1,'2022-12-27 13:38:13.399804','2022-12-27 13:38:15.172376',1,0),
(860,'C',1,'2022-12-27 13:50:46.215920','2022-12-27 13:50:49.153914',1,0),
(861,'C',1,'2022-12-27 15:30:44.931077','2022-12-27 15:30:50.336413',1,0),
(862,'C',1,'2022-12-27 16:38:15.641853','2022-12-27 16:38:20.688800',1,0),
(863,'E',1,'2022-12-27 16:38:21.478869','2022-12-27 16:38:21.478878',1,1),
(864,'E',1,'2022-12-27 17:12:18.363917','2022-12-27 17:12:18.363923',1,1),
(865,'C',1,'2022-12-27 19:20:20.465375','2022-12-27 19:20:23.594352',1,0),
(866,'E',1,'2022-12-27 19:20:24.727115','2022-12-27 19:20:40.875407',1,0),
(867,'C',1,'2022-12-27 22:28:36.952624','2022-12-27 22:28:44.235270',1,0),
(868,'E',1,'2022-12-27 22:28:45.189949','2022-12-27 22:29:26.974916',1,0),
(869,'C',1,'2022-12-27 22:31:09.221068','2022-12-27 22:31:44.466357',1,0),
(870,'C',1,'2022-12-27 22:31:44.763800','2022-12-27 22:31:52.031419',1,0),
(871,'D',1,'2022-12-27 22:31:52.387962','2022-12-27 22:31:58.602222',1,0),
(872,'E',1,'2022-12-27 22:31:59.055229','2022-12-27 22:31:59.055233',1,1),
(873,'E',1,'2022-12-27 22:44:27.651286','2022-12-27 22:44:27.651295',1,1),
(874,'E',1,'2022-12-27 22:45:20.151229','2022-12-27 22:45:20.151242',1,1),
(875,'E',1,'2022-12-27 22:46:01.850529','2022-12-27 22:46:01.850536',1,1),
(876,'E',1,'2022-12-27 22:47:15.263675','2022-12-27 22:47:15.263682',1,1),
(877,'C',1,'2022-12-27 22:50:06.460892','2022-12-27 22:50:08.389207',1,0),
(878,'C',1,'2022-12-27 22:50:41.076754','2022-12-27 22:50:41.076760',1,1),
(879,'E',1,'2022-12-27 22:51:33.617267','2022-12-27 22:51:48.689964',1,0),
(880,'C',1,'2022-12-27 22:52:37.524724','2022-12-27 22:52:39.831903',1,0),
(881,'E',1,'2022-12-27 22:52:40.177089','2022-12-27 22:52:40.177095',1,1),
(882,'E',1,'2022-12-27 22:57:56.454903','2022-12-27 22:58:12.720585',1,0),
(883,'D',1,'2022-12-27 22:58:13.283028','2022-12-27 22:58:19.098661',1,0),
(884,'C',1,'2022-12-27 22:58:19.717967','2022-12-27 22:58:19.717974',1,1),
(885,'C',1,'2022-12-27 22:59:05.332146','2022-12-27 22:59:24.240283',1,0),
(886,'D',1,'2022-12-27 22:59:24.754245','2022-12-27 22:59:28.326875',1,0),
(887,'D',1,'2022-12-27 22:59:28.776106','2022-12-27 22:59:35.127863',1,0),
(888,'E',1,'2022-12-27 22:59:35.616131','2022-12-27 22:59:35.616144',1,1),
(889,'D',1,'2022-12-27 23:34:20.245270','2022-12-27 23:34:24.148832',1,0),
(890,'E',1,'2022-12-27 23:34:25.335018','2022-12-27 23:34:25.335026',1,1),
(891,'E',1,'2022-12-27 23:41:17.790443','2022-12-27 23:42:19.307656',1,0),
(892,'D',1,'2022-12-27 23:42:20.078686','2022-12-27 23:42:21.318985',1,0),
(893,'C',1,'2022-12-27 23:42:23.673216','2022-12-27 23:42:24.282743',1,0),
(894,'D',1,'2022-12-27 23:42:24.755727','2022-12-27 23:42:25.484018',1,0),
(895,'E',1,'2022-12-27 23:42:25.800442','2022-12-27 23:42:26.438109',1,0),
(896,'C',1,'2022-12-27 23:42:27.024861','2022-12-27 23:42:29.678632',1,0),
(897,'E',1,'2022-12-27 23:42:29.881035','2022-12-27 23:42:30.508775',1,0),
(898,'D',1,'2022-12-27 23:42:31.012989','2022-12-27 23:42:31.290373',1,0),
(899,'C',1,'2022-12-27 23:42:31.512348','2022-12-27 23:42:34.085282',1,0),
(900,'C',1,'2022-12-28 10:22:02.187928','2022-12-28 10:22:13.295651',1,0),
(901,'C',1,'2022-12-28 10:22:13.715066','2022-12-28 10:22:13.715073',1,1),
(902,'C',1,'2022-12-28 15:03:30.557541','2022-12-28 15:03:34.001281',1,0),
(903,'E',1,'2022-12-28 15:03:34.517622','2022-12-28 15:03:34.517632',1,1),
(904,'C',1,'2022-12-29 12:09:58.453152','2022-12-29 12:10:01.192363',1,0),
(905,'C',1,'2022-12-29 12:40:35.920946','2022-12-29 12:40:39.814269',1,0),
(906,'C',1,'2022-12-29 13:20:13.257722','2022-12-29 13:20:16.870323',1,0),
(907,'C',1,'2022-12-29 13:20:18.512648','2022-12-29 13:20:34.056406',1,0),
(908,'C',1,'2022-12-29 15:38:08.329015','2022-12-29 15:38:08.329023',-1,1),
(909,'C',1,'2022-12-29 15:41:01.880106','2022-12-29 15:41:01.880112',-1,1),
(910,'D',1,'2022-12-29 15:42:09.869149','2022-12-29 15:42:09.869157',-1,1),
(911,'E',1,'2022-12-29 15:43:37.395489','2022-12-29 15:44:09.268400',-1,0),
(912,'E',1,'2022-12-29 15:44:10.559598','2022-12-29 15:44:10.559607',-1,1),
(913,'D',1,'2022-12-29 15:45:17.455984','2022-12-29 15:45:17.455992',-1,1),
(914,'C',1,'2022-12-29 15:46:06.563087','2022-12-29 15:46:06.563094',-1,1),
(915,'E',1,'2022-12-29 15:48:24.026268','2022-12-29 15:48:24.026276',-1,1),
(916,'E',1,'2022-12-29 15:50:25.187478','2022-12-29 15:50:25.187488',-1,1),
(917,'E',1,'2022-12-29 15:53:13.582034','2022-12-29 15:53:18.411641',-1,0),
(918,'C',1,'2022-12-29 15:53:22.842381','2022-12-29 15:53:25.838057',1,0),
(919,'C',1,'2022-12-29 15:58:46.877423','2022-12-29 15:59:01.471628',1,0),
(920,'D',1,'2022-12-29 15:59:03.259687','2022-12-29 15:59:08.916274',1,0),
(921,'E',1,'2022-12-29 15:59:09.897116','2022-12-29 15:59:09.897124',1,1),
(922,'E',1,'2022-12-29 16:02:01.034100','2022-12-29 16:02:01.034108',1,1),
(923,'C',1,'2022-12-29 21:28:54.902732','2022-12-29 21:29:00.351584',1,0),
(924,'E',1,'2022-12-29 21:29:00.916631','2022-12-29 21:29:00.916639',1,1),
(925,'E',1,'2022-12-29 21:30:03.351749','2022-12-29 21:30:03.351756',1,1),
(926,'C',1,'2022-12-29 21:37:51.531043','2022-12-29 21:37:53.720004',1,0),
(927,'E',1,'2022-12-29 21:37:54.277309','2022-12-29 21:38:25.421402',1,0),
(928,'E',1,'2022-12-29 21:38:26.391825','2022-12-29 21:38:26.391837',1,1),
(929,'E',1,'2022-12-29 21:43:53.239343','2022-12-29 21:44:34.810852',1,0),
(930,'E',1,'2022-12-29 21:45:55.067917','2022-12-29 21:46:02.689122',1,0),
(931,'C',1,'2022-12-30 11:32:39.253104','2022-12-30 11:32:43.766600',1,0),
(932,'E',1,'2022-12-30 11:32:44.242240','2022-12-30 11:32:44.242248',1,1),
(933,'E',1,'2022-12-30 11:37:09.714206','2022-12-30 11:37:09.714213',1,1),
(934,'E',1,'2022-12-30 11:41:04.127739','2022-12-30 11:41:04.127760',1,1),
(935,'E',1,'2022-12-30 12:40:51.626491','2022-12-30 12:51:56.637351',1,0),
(936,'C',1,'2022-12-30 13:20:14.363737','2022-12-30 13:20:16.560816',1,0),
(937,'E',1,'2022-12-30 13:20:17.115350','2022-12-30 13:20:17.115359',1,1),
(938,'E',1,'2022-12-30 13:31:51.001828','2022-12-30 13:31:51.001833',1,1),
(939,'E',1,'2022-12-30 13:34:57.408498','2022-12-30 13:34:57.408515',1,1),
(940,'E',1,'2022-12-30 13:39:40.758568','2022-12-30 13:39:40.758575',1,1),
(941,'E',1,'2022-12-30 13:45:37.012011','2022-12-30 13:45:37.012018',1,1),
(942,'E',1,'2022-12-30 14:05:35.035943','2022-12-30 14:05:35.035952',1,1),
(943,'E',1,'2022-12-30 14:16:11.248327','2022-12-30 14:16:11.248339',1,1),
(944,'C',1,'2023-01-01 11:15:58.923885','2023-01-01 11:16:01.234503',1,0),
(945,'E',1,'2023-01-01 11:16:01.729583','2023-01-01 11:17:04.152973',1,0),
(946,'C',1,'2023-01-01 11:17:11.982689','2023-01-01 11:17:16.667176',1,0),
(947,'E',1,'2023-01-01 11:17:17.158848','2023-01-01 11:17:17.158855',1,1),
(948,'C',1,'2023-01-01 11:28:33.776452','2023-01-01 11:28:35.989028',1,0),
(949,'E',1,'2023-01-01 11:28:36.412532','2023-01-01 11:29:10.487318',1,0),
(950,'C',1,'2023-01-01 12:19:29.402235','2023-01-01 12:19:31.831189',1,0),
(951,'C',1,'2023-01-01 12:19:32.261549','2023-01-01 12:19:32.261556',1,1),
(952,'C',1,'2023-01-01 12:21:00.852483','2023-01-01 12:21:00.852488',1,1),
(953,'C',1,'2023-01-01 12:27:20.438766','2023-01-01 12:27:20.438773',1,1),
(954,'C',1,'2023-01-01 12:30:36.387562','2023-01-01 12:31:21.874648',1,0),
(955,'C',1,'2023-01-01 12:31:22.453003','2023-01-01 12:31:34.661816',1,0),
(956,'C',1,'2023-01-01 12:31:35.163616','2023-01-01 12:31:53.500716',1,0),
(957,'C',1,'2023-01-01 12:31:54.036471','2023-01-01 12:31:54.036476',1,1),
(958,'C',1,'2023-01-01 12:36:09.015558','2023-01-01 12:36:13.282058',1,0),
(959,'C',1,'2023-01-01 12:36:13.658912','2023-01-01 12:36:13.658917',1,1),
(960,'C',1,'2023-01-01 12:38:59.536641','2023-01-01 12:39:13.259707',1,0),
(961,'C',1,'2023-01-01 12:39:13.713788','2023-01-01 12:39:13.713800',1,1),
(962,'C',1,'2023-01-01 12:45:45.400361','2023-01-01 12:45:49.361409',1,0),
(963,'C',1,'2023-01-01 12:45:49.779006','2023-01-01 12:45:49.779014',1,1),
(964,'C',1,'2023-01-01 12:48:19.700848','2023-01-01 12:48:19.700856',1,1),
(965,'C',1,'2023-01-01 12:53:23.846598','2023-01-01 12:53:31.140901',1,0),
(966,'C',1,'2023-01-01 12:53:31.563922','2023-01-01 12:54:24.855310',1,0),
(967,'C',1,'2023-01-01 12:54:26.629800','2023-01-01 12:54:26.629813',1,1),
(968,'C',1,'2023-01-01 13:02:22.044554','2023-01-01 13:02:22.044565',1,1),
(969,'C',1,'2023-01-01 13:08:40.583977','2023-01-01 13:08:51.349702',1,0),
(970,'C',1,'2023-01-01 13:08:51.848993','2023-01-01 13:09:04.957696',1,0),
(971,'C',1,'2023-01-01 13:09:05.523887','2023-01-01 13:09:13.533977',1,0),
(972,'C',1,'2023-01-01 13:09:13.974594','2023-01-01 13:09:13.974600',1,1),
(973,'C',1,'2023-01-01 13:14:15.948032','2023-01-01 13:14:15.948040',1,1),
(974,'C',1,'2023-01-01 13:15:32.500746','2023-01-01 13:15:32.500754',1,1),
(975,'C',1,'2023-01-01 13:16:13.479767','2023-01-01 13:16:13.479773',1,1),
(976,'C',1,'2023-01-01 13:19:57.944262','2023-01-01 13:19:57.944269',1,1),
(977,'C',1,'2023-01-01 13:22:16.653632','2023-01-01 13:22:16.653639',1,1),
(978,'C',1,'2023-01-01 13:23:50.651936','2023-01-01 13:25:19.083122',1,0),
(979,'C',1,'2023-01-01 19:23:16.211595','2023-01-01 19:25:10.995251',1,0),
(980,'C',1,'2023-01-01 19:25:11.410354','2023-01-01 19:25:48.998751',1,0),
(981,'D',1,'2023-01-01 19:25:49.545599','2023-01-01 19:25:49.545606',1,1),
(982,'D',1,'2023-01-01 19:27:13.113730','2023-01-01 19:27:16.447976',1,0),
(983,'C',1,'2023-01-01 19:27:17.181367','2023-01-01 19:27:17.181375',1,1),
(984,'C',1,'2023-01-01 19:27:46.374263','2023-01-01 19:28:29.779850',1,0),
(985,'C',1,'2023-01-01 19:28:30.272109','2023-01-01 19:28:30.272116',1,1),
(986,'C',1,'2023-01-01 19:28:39.040602','2023-01-01 19:28:39.040607',1,1),
(987,'C',1,'2023-01-01 19:30:21.995019','2023-01-01 19:30:21.995025',1,1),
(988,'C',1,'2023-01-01 19:32:35.835062','2023-01-01 19:32:35.835070',1,1),
(989,'C',1,'2023-01-01 19:38:06.495929','2023-01-01 19:38:48.338103',1,0),
(990,'C',1,'2023-01-01 19:38:48.790009','2023-01-01 19:38:48.790016',1,1),
(991,'C',1,'2023-01-01 19:39:14.287790','2023-01-01 19:39:14.287799',1,1),
(992,'C',1,'2023-01-03 16:55:57.343613','2023-01-03 16:57:13.204778',1,0),
(993,'C',1,'2023-01-03 16:57:14.241961','2023-01-03 16:57:26.125200',1,0),
(994,'C',1,'2023-01-03 16:57:48.312781','2023-01-03 16:58:13.414400',1,0),
(995,'C',1,'2023-01-03 16:58:13.912643','2023-01-03 16:58:39.725088',1,0),
(996,'C',1,'2023-01-03 16:59:05.595463','2023-01-03 16:59:08.177716',1,0),
(997,'C',1,'2023-01-03 16:59:08.721225','2023-01-03 16:59:18.905690',1,0),
(998,'C',1,'2023-01-03 16:59:19.570520','2023-01-03 16:59:24.632175',1,0),
(999,'C',1,'2023-01-03 16:59:25.251314','2023-01-03 16:59:25.251318',1,1),
(1000,'C',1,'2023-01-03 17:03:19.950629','2023-01-03 17:03:24.526012',1,0),
(1001,'C',1,'2023-01-03 17:03:51.206381','2023-01-03 17:04:23.167343',-1,0),
(1002,'D',1,'2023-01-03 17:04:23.739939','2023-01-03 17:04:45.269854',-1,0),
(1003,'E',1,'2023-01-03 17:04:45.891388','2023-01-03 17:04:45.891421',-1,1),
(1004,'C',1,'2023-01-04 11:25:52.540696','2023-01-04 11:26:06.191197',1,0),
(1005,'C',1,'2023-01-04 11:26:06.610638','2023-01-04 11:26:14.781769',1,0),
(1006,'D',1,'2023-01-04 11:26:15.311661','2023-01-04 11:26:31.113260',1,0),
(1007,'E',1,'2023-01-04 11:26:31.701342','2023-01-04 11:26:31.701349',1,1),
(1008,'C',1,'2023-01-04 11:30:46.551792','2023-01-04 11:30:52.950589',1,0),
(1009,'E',1,'2023-01-04 11:30:53.417604','2023-01-04 11:30:53.417612',1,1),
(1010,'E',1,'2023-01-04 11:36:26.676066','2023-01-04 11:36:49.020076',1,0),
(1011,'D',1,'2023-01-04 11:36:49.486624','2023-01-04 11:37:01.842827',1,0),
(1012,'C',1,'2023-01-04 11:37:02.331931','2023-01-04 11:37:20.071525',1,0),
(1013,'E',1,'2023-01-04 11:39:21.741197','2023-01-04 11:40:03.166008',-1,0),
(1014,'D',1,'2023-01-04 11:40:03.694287','2023-01-04 11:40:24.269024',-1,0),
(1015,'C',1,'2023-01-04 11:40:24.742084','2023-01-04 11:40:24.742117',-1,1),
(1016,'C',1,'2023-01-04 11:47:56.949740','2023-01-04 11:47:56.949748',-1,1),
(1017,'C',1,'2023-01-04 11:48:43.800911','2023-01-04 11:48:43.800918',-1,1),
(1018,'C',1,'2023-01-04 11:49:06.974099','2023-01-04 11:49:06.974108',-1,1),
(1019,'C',1,'2023-01-04 11:51:57.148993','2023-01-04 11:51:57.149000',-1,1),
(1020,'C',1,'2023-01-04 11:54:15.662764','2023-01-04 11:55:13.226689',-1,0),
(1021,'D',1,'2023-01-04 11:55:13.665373','2023-01-04 11:55:13.665381',-1,1),
(1022,'D',1,'2023-01-04 11:56:28.413434','2023-01-04 11:57:11.058285',-1,0),
(1023,'E',1,'2023-01-04 11:57:12.050228','2023-01-04 11:57:45.484765',-1,0),
(1024,'C',1,'2023-01-04 11:57:48.881255','2023-01-04 11:57:52.413741',1,0),
(1025,'C',1,'2023-01-04 11:57:52.745588','2023-01-04 11:57:58.078096',1,0),
(1026,'D',1,'2023-01-04 11:57:58.437243','2023-01-04 11:58:03.392166',1,0),
(1027,'E',1,'2023-01-04 11:58:03.838420','2023-01-04 11:58:03.838427',1,1),
(1028,'C',1,'2023-01-05 21:05:17.499625','2023-01-05 21:05:19.874939',1,0),
(1029,'C',1,'2023-01-06 11:37:10.694614','2023-01-06 11:37:13.413444',1,0),
(1030,'C',1,'2023-01-06 11:37:18.263302','2023-01-06 11:37:18.263308',1,1),
(1031,'C',1,'2023-01-06 11:38:59.399430','2023-01-06 11:39:01.497994',1,0),
(1032,'C',1,'2023-01-06 12:18:04.056172','2023-01-06 12:18:05.904853',1,0),
(1033,'C',1,'2023-01-06 16:07:22.879140','2023-01-06 16:07:25.132106',1,0);
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ws_predictions_client`
--

LOCK TABLES `ws_predictions_client` WRITE;
/*!40000 ALTER TABLE `ws_predictions_client` DISABLE KEYS */;
/*!40000 ALTER TABLE `ws_predictions_client` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'CAM-AI_GIT'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-06-03 12:27:38
