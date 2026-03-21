// ====================================
// 户外活动规划助手 - MongoDB 初始化脚本
// ====================================
// 使用方法：
// 1. 本地 MongoDB:
//    mongosh localhost:27017/outdoor_planner setup_mongodb.js
// 2. Docker MongoDB:
//    docker exec -i outdoor-mongodb mongosh outdoor_planner < setup_mongodb.js
// ====================================

// 切换到目标数据库
use outdoor_planner;

// 创建 reports 集合的索引
db.reports.createIndex({ user_id: 1, created_at: -1 });
db.reports.createIndex({ deleted_at: 1 });
db.reports.createIndex({ plan_name: "text", "content.summary": "text" });

// 创建验证规则的集合（可选，用于数据验证）
db.createCollection("reports", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["user_id", "plan_name", "trip_date", "overall_rating", "content"],
      properties: {
        user_id: { bsonType: "int" },
        plan_name: { bsonType: "string" },
        trip_date: { bsonType: "string" },
        overall_rating: { bsonType: "string" },
        content: { bsonType: "object" },
        created_at: { bsonType: "date" },
        deleted_at: { bsonType: ["null", "string"] }
      }
    }
  }
});

// 插入示例数据（可选）
// db.reports.insertOne({
//   user_id: 1,
//   plan_name: "示例计划",
//   trip_date: "2026-03-22",
//   overall_rating: "推荐",
//   content: { summary: "这是一个示例报告" },
//   created_at: new Date(),
//   deleted_at: null
// });

print("MongoDB 初始化完成！");
print("数据库: outdoor_planner");
print("集合: reports (已创建索引)");
