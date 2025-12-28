UPDATE `Product`
SET `currentQty` = 0
WHERE `currentQty` IS NULL;

/*
  Warnings:

  - A unique constraint covering the columns `[refType,refId,sku]` on the table `InventoryLedger` will be added. If there are existing duplicate values, this will fail.
  - Made the column `currentQty` on table `product` required. This step will fail if there are existing NULL values in that column.

*/
-- AlterTable
ALTER TABLE `product` MODIFY `currentQty` INTEGER NOT NULL DEFAULT 0;

-- CreateIndex
CREATE UNIQUE INDEX `InventoryLedger_refType_refId_sku_key` ON `InventoryLedger`(`refType`, `refId`, `sku`);
