# ElastiCache Redis for AI DriveThru (DISABLED - Expensive!)
# Redis is disabled by default to save costs (~$30/month)
# Your app will use in-memory caching instead

# Uncomment the lines below ONLY if you want to enable Redis (NOT RECOMMENDED)
# resource "aws_elasticache_subnet_group" "main" {
#   count = var.enable_redis ? 1 : 0
#   name       = "${local.project_name}-redis-subnet-group"
#   subnet_ids = aws_subnet.private[*].id
#   tags = local.common_tags
# }

# resource "aws_elasticache_replication_group" "redis" {
#   count = var.enable_redis ? 1 : 0
#   replication_group_id = "${local.project_name}-redis"
#   description = "Redis cluster for AI DriveThru"
#   node_type = "cache.t3.micro"
#   port = 6379
#   parameter_group_name = "default.redis7"
#   num_cache_clusters = 1
#   automatic_failover_enabled = false
#   multi_az_enabled = false
#   subnet_group_name = aws_elasticache_subnet_group.main[0].name
#   security_group_ids = [aws_security_group.redis.id]
#   snapshot_retention_limit = 5
#   snapshot_window = "03:00-05:00"
#   maintenance_window = "sun:05:00-sun:07:00"
#   at_rest_encryption_enabled = true
#   transit_encryption_enabled = false
#   tags = local.common_tags
# }
