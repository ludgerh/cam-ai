-- MySQL dump 10.19  Distrib 10.3.36-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: CAM-AI_NEW
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
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$320000$qNLhQwFZlSenPndPEOhpgq$JUgVnfc3Pag91aDbq5HSrKebkjBGSwJKZMWJxCYuGQU=','2022-09-18 10:26:51.367000',1,'admin','admin','admin','ludger@booker-hellerhoff.de',1,1,'2022-01-23 19:32:53.722000');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
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
  `eve_all_predictions` tinyint(1) NOT NULL,
  `eve_school_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `streams_stream_eve_school_id_3e307b1b_fk_tf_workers_school_id` (`eve_school_id`),
  CONSTRAINT `streams_stream_eve_school_id_3e307b1b_fk_tf_workers_school_id` FOREIGN KEY (`eve_school_id`) REFERENCES `tf_workers_school` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tf_workers_school`
--

LOCK TABLES `tf_workers_school` WRITE;
/*!40000 ALTER TABLE `tf_workers_school` DISABLE KEYS */;
INSERT INTO `tf_workers_school` VALUES (1,'School 1','data/models/c_model_1/',1000,'2022-07-14 20:13:27.039000',1,'1e-6','1e-6',1,'efficientnetv2b0',1,0,0,2,1,8,6,1,1);
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
  `wsname` varchar(30) NOT NULL,
  `wspass` varchar(30) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tf_workers_worker`
--

LOCK TABLES `tf_workers_worker` WRITE;
/*!40000 ALTER TABLE `tf_workers_worker` DISABLE KEYS */;
INSERT INTO `tf_workers_worker` VALUES (1,1,'TF-Worker 1',8,0.1,64,20,0,-1,0,0,1,'wss://django.cam-ai.de/','myname','mypass');
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
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tools_setting`
--

LOCK TABLES `tools_setting` WRITE;
/*!40000 ALTER TABLE `tools_setting` DISABLE KEYS */;
INSERT INTO `tools_setting` VALUES (1,'loglevel','INFO','No Comment'),(2,'emulatestatic','0','No Comment'),(3,'version','0.6.1','No Comment'),(5,'local_trainer','0','No Comment');
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
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trainers_trainer`
--

LOCK TABLES `trainers_trainer` WRITE;
/*!40000 ALTER TABLE `trainers_trainer` DISABLE KEYS */;
INSERT INTO `trainers_trainer` VALUES (1,1,'Trainer 1',3,0,0,'00:00:00','24:00:00',1,'wss://django.cam-ai.de/');
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
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
  `counter` int(11) NOT NULL,
  `school_id` bigint(20) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `users_userinfo_school_id_3ee6112c_fk_tf_workers_school_id` (`school_id`),
  KEY `users_userinfo_user_id_6acffaf6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `users_userinfo_school_id_3ee6112c_fk_tf_workers_school_id` FOREIGN KEY (`school_id`) REFERENCES `tf_workers_school` (`id`),
  CONSTRAINT `users_userinfo_user_id_6acffaf6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_userinfo`
--

LOCK TABLES `users_userinfo` WRITE;
/*!40000 ALTER TABLE `users_userinfo` DISABLE KEYS */;
INSERT INTO `users_userinfo` VALUES (1,0,1,1);
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

-- Dump completed on 2022-11-04 20:50:13
