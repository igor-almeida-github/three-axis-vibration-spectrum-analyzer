SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema fft_dados
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema fft_dados
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `fft_dados` DEFAULT CHARACTER SET utf8 ;
USE `fft_dados` ;

-- -----------------------------------------------------
-- Table `fft_dados`.`registros_de_vibracao`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `fft_dados`.`registros_de_vibracao` ;

CREATE TABLE IF NOT EXISTS `fft_dados`.`registros_de_vibracao` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(50) NOT NULL,
  `data` DATE NOT NULL,
  `hora` TIME NOT NULL,
  `diretorio_entradas_rede_neural` VARCHAR(200) NOT NULL,
  `quantidade_de_ffts_coletadas` INT NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `fft_dados`.`descricoes`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `fft_dados`.`descricoes` ;

CREATE TABLE IF NOT EXISTS `fft_dados`.`descricoes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `id_registro_de_vibracao` INT NOT NULL,
  `descricao` VARCHAR(200) NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_descricoes_1_idx` (`id_registro_de_vibracao` ASC) VISIBLE,
  UNIQUE INDEX `id_registro_de_vibracao_UNIQUE` (`id_registro_de_vibracao` ASC) VISIBLE,
  CONSTRAINT `fk_descricoes_1`
    FOREIGN KEY (`id_registro_de_vibracao`)
    REFERENCES `fft_dados`.`registros_de_vibracao` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
