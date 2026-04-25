package com.rembo.healthcheck;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;

public class HealthCheckReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) {
            SharedPreferences prefs = context.getSharedPreferences(
                "rembo_sentinel_prefs", Context.MODE_PRIVATE);
            if (!prefs.getBoolean("health_popup_silenced", false)) {
                // Check if popup request exists from Sentinel daemon
                java.io.File popupRequest = new java.io.File(
                    "/data/rembo-sentinel/popup_request.json");
                if (popupRequest.exists()) {
                    Intent healthIntent = new Intent(context, HealthCheckActivity.class);
                    healthIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    context.startActivity(healthIntent);
                }
            }
        }
    }
}
