/*
 * REMBO-Bliss-os Sovereign Edition
 * Weekly Health Check GUI Activity
 * Lead Architect: FERAS-AL-ABBADI
 */
package com.rembo.healthcheck;

import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.graphics.Color;
import android.graphics.Typeface;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;

public class HealthCheckActivity extends Activity {

    private static final String PREFS_NAME = "rembo_sentinel_prefs";
    private static final String KEY_SILENCED = "health_popup_silenced";
    private static final String HEALTH_LOG = "/data/rembo-sentinel/health.log";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        if (prefs.getBoolean(KEY_SILENCED, false)) {
            finish();
            return;
        }

        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        // Build UI programmatically
        ScrollView scrollView = new ScrollView(this);
        scrollView.setBackgroundColor(Color.parseColor("#1a1a2e"));
        scrollView.setPadding(48, 48, 48, 48);

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(32, 32, 32, 32);

        // Title
        TextView title = new TextView(this);
        title.setText("REMBO-Bliss-os");
        title.setTextColor(Color.parseColor("#e94560"));
        title.setTextSize(28);
        title.setTypeface(null, Typeface.BOLD);
        layout.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("Weekly System Health Check");
        subtitle.setTextColor(Color.parseColor("#16213e"));
        subtitle.setTextSize(16);
        subtitle.setPadding(0, 0, 0, 32);
        subtitle.setTextColor(Color.parseColor("#aaaaaa"));
        layout.addView(subtitle);

        // Health Report Content
        TextView reportView = new TextView(this);
        reportView.setTextColor(Color.parseColor("#e0e0e0"));
        reportView.setTextSize(14);
        reportView.setTypeface(Typeface.MONOSPACE);
        reportView.setPadding(0, 16, 0, 32);

        String reportContent = readHealthReport();
        reportView.setText(reportContent);
        layout.addView(reportView);

        // Score display
        TextView scoreView = new TextView(this);
        scoreView.setTextSize(24);
        scoreView.setTypeface(null, Typeface.BOLD);
        scoreView.setPadding(0, 16, 0, 32);
        if (reportContent.contains("100/100")) {
            scoreView.setText("System Score: 100/100");
            scoreView.setTextColor(Color.parseColor("#00ff88"));
        } else {
            scoreView.setText("System Score: DEGRADED");
            scoreView.setTextColor(Color.parseColor("#ff4444"));
        }
        layout.addView(scoreView);

        // Silence checkbox
        CheckBox silenceCheckbox = new CheckBox(this);
        silenceCheckbox.setText("Do not show this again");
        silenceCheckbox.setTextColor(Color.parseColor("#888888"));
        silenceCheckbox.setTextSize(14);
        silenceCheckbox.setPadding(0, 32, 0, 16);
        layout.addView(silenceCheckbox);

        // Close button
        Button closeBtn = new Button(this);
        closeBtn.setText("Close");
        closeBtn.setBackgroundColor(Color.parseColor("#e94560"));
        closeBtn.setTextColor(Color.WHITE);
        closeBtn.setTextSize(16);
        closeBtn.setPadding(32, 16, 32, 16);
        closeBtn.setOnClickListener(v -> {
            if (silenceCheckbox.isChecked()) {
                prefs.edit().putBoolean(KEY_SILENCED, true).apply();
                // Also create the sentinel no_popup file
                try {
                    new File("/data/rembo-sentinel/no_popup").createNewFile();
                } catch (IOException e) {
                    // Best effort
                }
            }
            finish();
        });
        layout.addView(closeBtn);

        // Architect credit
        TextView credit = new TextView(this);
        credit.setText("\nLead Architect: FERAS-AL-ABBADI\nInstagram: @684ao");
        credit.setTextColor(Color.parseColor("#555555"));
        credit.setTextSize(12);
        credit.setPadding(0, 32, 0, 0);
        layout.addView(credit);

        scrollView.addView(layout);
        setContentView(scrollView);
    }

    private String readHealthReport() {
        StringBuilder sb = new StringBuilder();
        File reportFile = new File(HEALTH_LOG);

        if (!reportFile.exists()) {
            return "No health report available.\nRun: rembo-sentinel health";
        }

        try (BufferedReader br = new BufferedReader(new FileReader(reportFile))) {
            String line;
            while ((line = br.readLine()) != null) {
                sb.append(line).append("\n");
            }
        } catch (IOException e) {
            return "Error reading health report: " + e.getMessage();
        }

        return sb.toString();
    }

    /**
     * BroadcastReceiver to trigger health check popup
     */
    public static class HealthCheckReceiver extends BroadcastReceiver {
        @Override
        public void onReceive(Context context, Intent intent) {
            if ("com.rembo.HEALTH_CHECK".equals(intent.getAction())) {
                SharedPreferences prefs = context.getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
                if (!prefs.getBoolean(KEY_SILENCED, false)) {
                    Intent activityIntent = new Intent(context, HealthCheckActivity.class);
                    activityIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    context.startActivity(activityIntent);
                }
            }
        }
    }
}
