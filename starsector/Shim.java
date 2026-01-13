import java.io.*;
import java.net.*;
import com.fs.starfarer.combat.CombatMain;

public class Shim {
    public static void main(String[] args) throws Exception {
        System.out.println("[SHIM] Starting manual setup...");
        
        new File("data/config").mkdirs();
        
        download("data/config/settings.json", "data/config/settings.json");
        download("console_log4j.properties", "console_log4j.properties");
        download("data/config/sounds.json", "data/config/sounds.json");
        
        System.out.println("[SHIM] Launching Starsector...");
        try {
            CombatMain.main(args);
        } catch (Throwable t) {
            System.err.println("[SHIM] Crash in CombatMain:");
            t.printStackTrace();
        }
    }
    
    private static void download(String urlPath, String localPath) {
        try {
            URL url = new URL("http://127.0.0.1:8091/" + urlPath);
            InputStream in = url.openStream();
            FileOutputStream out = new FileOutputStream(localPath);
            byte[] buf = new byte[4096];
            int n;
            while ((n = in.read(buf)) > 0) {
                out.write(buf, 0, n);
            }
            in.close();
            out.close();
            System.out.println("[SHIM] Saved " + localPath);
        } catch (Exception e) {
            System.err.println("[SHIM] Error downloading " + urlPath + ": " + e);
        }
    }
}
