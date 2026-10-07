GRANT	INSERT	ON	ops.CustomerQuarantine	TO northstar_pipeline;
GRANT	INSERT	ON	ops.PipelineBatches	TO northstar_pipeline;
GRANT	SELECT	ON	ops.PipelineBatches	TO northstar_pipeline;
GRANT	UPDATE	ON	ops.PipelineBatches	TO northstar_pipeline;
GRANT	INSERT	ON	ops.PipelineEvents	TO northstar_pipeline;
GRANT	INSERT	ON	ops.PipelineRuns	TO northstar_pipeline;
GRANT	SELECT	ON	ops.PipelineRuns	TO northstar_pipeline;
GRANT	UPDATE	ON	ops.PipelineRuns	TO northstar_pipeline;
GRANT	INSERT	ON	ops.PipelineStageRuns	TO northstar_pipeline;
GRANT	SELECT	ON	ops.PipelineStageRuns	TO northstar_pipeline;
GRANT	UPDATE	ON	ops.PipelineStageRuns	TO northstar_pipeline;
GRANT	INSERT	ON	raw.Customers	TO northstar_pipeline;
GRANT	SELECT	ON	raw.Customers	TO northstar_pipeline;
GRANT	INSERT	ON	raw.CustomerBatchStage	TO northstar_pipeline;
GRANT	SELECT	ON	raw.CustomerBatchStage	TO northstar_pipeline;
GRANT   DELETE  ON  raw.CustomerBatchStage  TO northstar_pipeline;
GRANT	EXECUTE	ON	raw.usp_LoadCustomersForBatch	TO northstar_pipeline;
GRANT	EXECUTE	ON	silver.usp_LoadCustomers	TO northstar_pipeline;

GRANT SELECT, INSERT, DELETE ON OBJECT::raw.Products TO northstar_pipeline;
GRANT SELECT, INSERT, DELETE ON OBJECT::raw.ProductBatchStage TO northstar_pipeline;
GRANT EXECUTE ON OBJECT::raw.usp_LoadProductsForBatch TO northstar_pipeline;
-- GRANT SELECT, INSERT, UPDATE ON OBJECT::silver.Products TO northstar_pipeline;
GRANT EXECUTE ON OBJECT::silver.usp_LoadProducts TO northstar_pipeline;

GRANT SELECT, INSERT, DELETE ON OBJECT::raw.Orders TO northstar_pipeline;
GRANT SELECT, INSERT, DELETE ON OBJECT::raw.OrderBatchStage TO northstar_pipeline;
GRANT EXECUTE ON OBJECT::raw.usp_LoadOrdersForBatch TO northstar_pipeline;

GRANT SELECT, INSERT, DELETE ON OBJECT::ops.OrderQuarantine TO northstar_pipeline;
GRANT	EXECUTE	ON	silver.usp_LoadOrders	TO northstar_pipeline;

GRANT SELECT, INSERT, DELETE ON OBJECT::raw.OrderItems TO northstar_pipeline;
GRANT SELECT, INSERT, DELETE ON OBJECT::raw.OrderItemBatchStage TO northstar_pipeline;
GRANT SELECT, INSERT, DELETE ON OBJECT::ops.OrderItemQuarantine TO northstar_pipeline;
GRANT EXECUTE ON OBJECT::raw.usp_LoadOrderItemsForBatch TO northstar_pipeline;
GRANT	EXECUTE	ON	silver.usp_LoadOrderItems	TO northstar_pipeline;

GRANT SELECT, INSERT, DELETE ON OBJECT::raw.Payments TO northstar_pipeline;
GRANT SELECT, INSERT, DELETE ON OBJECT::raw.PaymentBatchStage TO northstar_pipeline;
GRANT EXECUTE ON OBJECT::raw.usp_LoadPaymentsForBatch TO northstar_pipeline;
GRANT SELECT, INSERT, DELETE ON OBJECT::ops.PaymentQuarantine TO northstar_pipeline;
GRANT	EXECUTE	ON	silver.usp_LoadPayments	TO northstar_pipeline;