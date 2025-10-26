/*
  Warnings:

  - You are about to drop the column `idempotencyKey` on the `product` table. All the data in the column will be lost.

*/
-- DropIndex
DROP INDEX `Product_idempotencyKey_key` ON `product`;

-- AlterTable
ALTER TABLE `product` DROP COLUMN `idempotencyKey`;
