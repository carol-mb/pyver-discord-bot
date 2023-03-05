-- phpMyAdmin SQL Dump
-- version 4.6.6deb5
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: 29 Aug 2021 la 14:24
-- Versiune server: 10.3.27-MariaDB-0+deb10u1
-- PHP Version: 7.3.27-1~deb10u1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `pyv2`
--

-- --------------------------------------------------------

--
-- Structura de tabel pentru tabelul `autoroles`
--

CREATE TABLE `autoroles` (
  `guild_id` bigint(20) NOT NULL,
  `role_id` bigint(20) NOT NULL,
  `receive_after` int(11) NOT NULL,
  `remove_after` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Structura de tabel pentru tabelul `bannedbackuproles`
--

CREATE TABLE `bannedbackuproles` (
  `guild_id` bigint(20) NOT NULL,
  `member_id` bigint(20) NOT NULL,
  `role_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


--
-- Structura de tabel pentru tabelul `bannedmembers`
--

CREATE TABLE `bannedmembers` (
  `guild_id` bigint(20) NOT NULL,
  `member_id` bigint(20) NOT NULL,
  `reason` varchar(128) NOT NULL DEFAULT 'no reason'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


--
-- Structura de tabel pentru tabelul `immunity`
--

CREATE TABLE `immunity` (
  `guild_id` bigint(20) NOT NULL,
  `member_id` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


--
-- Structura de tabel pentru tabelul `poll_answers`
--

CREATE TABLE `poll_answers` (
  `q_id` int(11) NOT NULL,
  `guild_id` bigint(20) NOT NULL,
  `emoji` varchar(64) NOT NULL,
  `answer` varchar(128) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Salvarea datelor din tabel `poll_answers`
--

--
-- Structura de tabel pentru tabelul `poll_questions`
--

CREATE TABLE `poll_questions` (
  `id` int(11) NOT NULL,
  `guild_id` bigint(20) NOT NULL,
  `channel_id` bigint(20) NOT NULL DEFAULT 0,
  `message_id` bigint(20) NOT NULL DEFAULT 0,
  `question` varchar(256) NOT NULL,
  `endtime` datetime NOT NULL DEFAULT current_timestamp(),
  `status` varchar(32) NOT NULL DEFAULT 'not started'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


--
-- Structura de tabel pentru tabelul `serverconfigs`
--

CREATE TABLE `serverconfigs` (
  `guild_id` bigint(20) NOT NULL,
  `bot_prefix` varchar(8) NOT NULL DEFAULT '>',
  `ban_role_id` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Structura de tabel pentru tabelul `verify`
--

CREATE TABLE `verify` (
  `guild_id` bigint(20) NOT NULL,
  `channel_id` bigint(20) NOT NULL,
  `message_id` bigint(20) NOT NULL,
  `role_id` bigint(20) NOT NULL,
  `emoji` varchar(256) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Structura de tabel pentru tabelul `voice_activity`
--

CREATE TABLE `voice_activity` (
  `guild_id` bigint(20) NOT NULL,
  `member_id` bigint(20) NOT NULL,
  `time_connected` int(11) NOT NULL,
  `datetime` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Structura de tabel pentru tabelul `voice_roles`
--

CREATE TABLE `voice_roles` (
  `guild_id` bigint(20) NOT NULL,
  `role_id` bigint(20) NOT NULL,
  `time_connected` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `poll_questions`
--
ALTER TABLE `poll_questions`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `serverconfigs`
--
ALTER TABLE `serverconfigs`
  ADD PRIMARY KEY (`guild_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `poll_questions`
--
ALTER TABLE `poll_questions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
