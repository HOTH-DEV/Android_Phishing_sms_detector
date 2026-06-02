package com.pfe.phishingdetector.data

import androidx.room.Dao
import androidx.room.Database
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.RoomDatabase
import kotlinx.coroutines.flow.Flow

/** A single stored analysis result (local history). */
@Entity(tableName = "analyses")
data class AnalysisEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val content: String,
    val score: Int,
    val verdict: String,
    val reasons: String,        // reasons joined by " | "
    val timestamp: Long = System.currentTimeMillis()
)

@Dao
interface AnalysisDao {
    @Insert
    suspend fun insert(item: AnalysisEntity)

    @Query("SELECT * FROM analyses ORDER BY timestamp DESC")
    fun observeAll(): Flow<List<AnalysisEntity>>

    @Query("SELECT COUNT(*) FROM analyses WHERE verdict = :verdict")
    fun countByVerdict(verdict: String): Flow<Int>

    @Query("DELETE FROM analyses")
    suspend fun clear()
}

@Database(entities = [AnalysisEntity::class], version = 1, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun analysisDao(): AnalysisDao
}
