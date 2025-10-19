import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.awt.image.BufferedImage;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public class Foxen3D extends JPanel implements Runnable, KeyListener {
    private static final int SCREEN_WIDTH = 800;
    private static final int SCREEN_HEIGHT = 600;
    private static final int HALF_HEIGHT = SCREEN_HEIGHT / 2;
    private static final double FOV = Math.PI / 3;
    private static final double HALF_FOV = FOV / 2;
    private static final int MAX_DEPTH = 20;
    private static final double MOVE_SPEED = 0.08; // Немного уменьшил скорость для лучшего контроля
    private static final double ROTATION_SPEED = 0.05;

    private BufferedImage buffer;
    private boolean running = true;
    
    private List<BufferedImage> wallTextures = new ArrayList<>();
    private List<Entity> entities = new ArrayList<>();
    private int[][] map = {
        {1, 1, 1, 1, 1, 1, 1},
        {1, 0, 0, 2, 0, 0, 1},
        {1, 0, 0, 0, 0, 0, 1},
        {1, 0, 0, 3, 0, 0, 1},
        {1, 0, 0, 0, 0, 0, 1},
        {1, 0, 0, 0, 0, 0, 1},
        {1, 1, 1, 1, 1, 1, 1}
    };
    
    private double playerX = 1.5;
    private double playerY = 1.5;
    private double playerAngle = 0.0;
    private int playerHealth = 100;
    private int playerScore = 0;
    private final Random random = new Random();
    
    private boolean[] keys = new boolean[256];
    
    // FPS контроллер
    private final int TARGET_FPS = 30;
    private final long OPTIMAL_TIME = 1000000000 / TARGET_FPS;

    public Foxen3D() {
        setPreferredSize(new Dimension(SCREEN_WIDTH, SCREEN_HEIGHT));
        buffer = new BufferedImage(SCREEN_WIDTH, SCREEN_HEIGHT, BufferedImage.TYPE_INT_RGB);
        
        generateTextures();
        createEntities();
        addKeyListener(this);
        setFocusable(true);
        requestFocusInWindow();
    }

    private void generateTextures() {
        for (int i = 0; i < 3; i++) {
            wallTextures.add(generateWallTexture());
        }
    }

    private BufferedImage generateWallTexture() {
        BufferedImage texture = new BufferedImage(64, 64, BufferedImage.TYPE_INT_RGB);
        Color baseColor = new Color(
            random.nextInt(51) + 150,
            random.nextInt(51) + 100,
            random.nextInt(51) + 50
        );

        for (int y = 0; y < 64; y++) {
            for (int x = 0; x < 64; x++) {
                int brickX = x % 16;
                int brickY = y % 16;

                Color color;
                if (brickX == 0 || brickY == 0 || brickX == 15 || brickY == 15) {
                    color = new Color(
                        Math.max(0, baseColor.getRed() - 50),
                        Math.max(0, baseColor.getGreen() - 50),
                        Math.max(0, baseColor.getBlue() - 50)
                    );
                } else {
                    int variation = random.nextInt(61) - 30;
                    color = new Color(
                        clamp(baseColor.getRed() + variation),
                        clamp(baseColor.getGreen() + variation),
                        clamp(baseColor.getBlue() + variation)
                    );
                }

                if (random.nextFloat() < 0.1) {
                    int noise = random.nextInt(41) - 20;
                    color = new Color(
                        clamp(color.getRed() + noise),
                        clamp(color.getGreen() + noise),
                        clamp(color.getBlue() + noise)
                    );
                }
                texture.setRGB(x, y, color.getRGB());
            }
        }
        return texture;
    }

    private int clamp(int value) {
        return Math.max(0, Math.min(255, value));
    }

    private void createEntities() {
        entities.add(new Entity(2.5, 2.5, "enemy", generateEntityTexture("enemy")));
        entities.add(new Entity(1.5, 1.5, "item", generateEntityTexture("item")));
        entities.add(new Entity(4.5, 3.5, "item", generateEntityTexture("item")));
        entities.add(new Entity(3.5, 5.5, "decor", generateEntityTexture("decor")));
        entities.add(new Entity(5.5, 1.5, "decor", generateEntityTexture("decor")));
    }

    private BufferedImage generateEntityTexture(String type) {
        BufferedImage texture = new BufferedImage(64, 64, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = texture.createGraphics();
        
        switch (type) {
            case "enemy":
                drawEnemy(g);
                break;
            case "item":
                drawItem(g);
                break;
            case "decor":
                drawDecor(g);
                break;
        }
        g.dispose();
        return texture;
    }

    private void drawEnemy(Graphics2D g) {
        g.setColor(new Color(200, 50, 50));
        g.fillOval(12, 12, 40, 40);
        
        g.setColor(new Color(150, 100, 100));
        g.fillOval(20, 10, 24, 24);
        
        g.setColor(Color.WHITE);
        g.fillOval(25, 15, 8, 8);
        g.fillOval(35, 15, 8, 8);
        
        g.setColor(Color.BLACK);
        g.fillOval(27, 17, 4, 4);
        g.fillOval(37, 17, 4, 4);
        
        g.setColor(new Color(200, 50, 50));
        g.fillRect(10, 40, 44, 10);
    }

    private void drawItem(Graphics2D g) {
        if (random.nextBoolean()) {
            // Health pack
            g.setColor(new Color(255, 50, 50));
            g.fillRect(20, 10, 24, 44);
            g.setColor(Color.WHITE);
            g.fillRect(24, 14, 16, 36);
            g.setColor(new Color(255, 50, 50));
            g.fillRect(28, 18, 8, 28);
        } else {
            // Ammo
            g.setColor(new Color(200, 200, 50));
            g.fillRect(15, 10, 34, 44);
            g.setColor(new Color(100, 100, 100));
            for (int i = 0; i < 3; i++) {
                g.fillRect(20, 15 + i * 12, 24, 8);
            }
        }
    }

    private void drawDecor(Graphics2D g) {
        g.setColor(new Color(150, 100, 50));
        g.fillRect(20, 10, 24, 54);
        g.setColor(new Color(100, 70, 30));
        for (int i = 0; i < 3; i++) {
            g.fillRect(22, 15 + i * 15, 20, 5);
        }
    }

    @Override
    public void run() {
        long lastLoopTime = System.nanoTime();
        
        while (running) {
            long now = System.nanoTime();
            long updateLength = now - lastLoopTime;
            lastLoopTime = now;
            
            update();
            render();
            repaint();
            
            // Ограничитель FPS
            long renderTime = (System.nanoTime() - lastLoopTime);
            long sleepTime = (OPTIMAL_TIME - renderTime) / 1000000;
            
            if (sleepTime > 0) {
                try {
                    Thread.sleep(sleepTime);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
        }
    }

    private void update() {
        // Handle rotation
        if (keys[KeyEvent.VK_LEFT]) {
            playerAngle -= ROTATION_SPEED;
        }
        if (keys[KeyEvent.VK_RIGHT]) {
            playerAngle += ROTATION_SPEED;
        }

        // Handle movement
        double moveX = Math.cos(playerAngle) * MOVE_SPEED;
        double moveY = Math.sin(playerAngle) * MOVE_SPEED;
        double strafeX = Math.cos(playerAngle + Math.PI/2) * MOVE_SPEED;
        double strafeY = Math.sin(playerAngle + Math.PI/2) * MOVE_SPEED;

        if (keys[KeyEvent.VK_UP] || keys[KeyEvent.VK_W]) {
            movePlayer(moveX, moveY);
        }
        if (keys[KeyEvent.VK_DOWN] || keys[KeyEvent.VK_S]) {
            movePlayer(-moveX, -moveY);
        }
        if (keys[KeyEvent.VK_A]) {
            movePlayer(-strafeX, -strafeY);
        }
        if (keys[KeyEvent.VK_D]) {
            movePlayer(strafeX, strafeY);
        }

        // Update entities
        for (Entity entity : entities) {
            entity.update(playerX, playerY);
        }
    }

    private void movePlayer(double dx, double dy) {
        double newX = playerX + dx;
        double newY = playerY + dy;

        // Улучшенная проверка коллизий - проверяем не только целые координаты
        // но и область вокруг игрока с небольшим зазором
        double collisionBuffer = 0.2; // Зазор для предотвращения застревания в стенах
        
        boolean canMoveX = true;
        boolean canMoveY = true;
        
        // Проверяем коллизии по X
        if (dx != 0) {
            int mapX1 = (int)(newX - collisionBuffer);
            int mapX2 = (int)(newX + collisionBuffer);
            int mapY1 = (int)(playerY - collisionBuffer);
            int mapY2 = (int)(playerY + collisionBuffer);
            
            if (mapX1 >= 0 && mapX1 < map.length && mapY1 >= 0 && mapY1 < map[0].length) {
                if (map[mapX1][mapY1] != 0) canMoveX = false;
            }
            if (mapX1 >= 0 && mapX1 < map.length && mapY2 >= 0 && mapY2 < map[0].length) {
                if (map[mapX1][mapY2] != 0) canMoveX = false;
            }
            if (mapX2 >= 0 && mapX2 < map.length && mapY1 >= 0 && mapY1 < map[0].length) {
                if (map[mapX2][mapY1] != 0) canMoveX = false;
            }
            if (mapX2 >= 0 && mapX2 < map.length && mapY2 >= 0 && mapY2 < map[0].length) {
                if (map[mapX2][mapY2] != 0) canMoveX = false;
            }
        }
        
        // Проверяем коллизии по Y
        if (dy != 0) {
            int mapX1 = (int)(playerX - collisionBuffer);
            int mapX2 = (int)(playerX + collisionBuffer);
            int mapY1 = (int)(newY - collisionBuffer);
            int mapY2 = (int)(newY + collisionBuffer);
            
            if (mapX1 >= 0 && mapX1 < map.length && mapY1 >= 0 && mapY1 < map[0].length) {
                if (map[mapX1][mapY1] != 0) canMoveY = false;
            }
            if (mapX1 >= 0 && mapX1 < map.length && mapY2 >= 0 && mapY2 < map[0].length) {
                if (map[mapX1][mapY2] != 0) canMoveY = false;
            }
            if (mapX2 >= 0 && mapX2 < map.length && mapY1 >= 0 && mapY1 < map[0].length) {
                if (map[mapX2][mapY1] != 0) canMoveY = false;
            }
            if (mapX2 >= 0 && mapX2 < map.length && mapY2 >= 0 && mapY2 < map[0].length) {
                if (map[mapX2][mapY2] != 0) canMoveY = false;
            }
        }
        
        // Применяем движение
        if (canMoveX) {
            playerX = newX;
        }
        if (canMoveY) {
            playerY = newY;
        }
    }

    private void render() {
        Graphics2D g2d = buffer.createGraphics();
        
        // Clear screen
        g2d.setColor(Color.BLACK);
        g2d.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);

        renderFloorCeiling(g2d);
        renderWalls(g2d);
        renderEntities(g2d);
        renderHUD(g2d);
        
        g2d.dispose();
    }

    private void renderFloorCeiling(Graphics2D g2d) {
        g2d.setColor(new Color(120, 120, 200));
        g2d.fillRect(0, 0, SCREEN_WIDTH, HALF_HEIGHT);
        g2d.setColor(new Color(80, 80, 80));
        g2d.fillRect(0, HALF_HEIGHT, SCREEN_WIDTH, HALF_HEIGHT);
    }

    private void renderWalls(Graphics2D g2d) {
        for (int x = 0; x < SCREEN_WIDTH; x++) {
            double rayAngle = playerAngle + Math.atan2(x - SCREEN_WIDTH / 2.0, SCREEN_WIDTH / (2 * Math.tan(HALF_FOV)));
            RayResult result = castRay(rayAngle);

            if (result.distance < Double.MAX_VALUE) {
                double dist = result.distance * Math.cos(playerAngle - rayAngle);
                int wallHeight = Math.min((int)(SCREEN_HEIGHT / dist), SCREEN_HEIGHT * 2);

                double wallX;
                if (result.side == 0) {
                    wallX = playerY + dist * Math.sin(rayAngle);
                } else {
                    wallX = playerX + dist * Math.cos(rayAngle);
                }
                wallX %= 1;
                if (wallX < 0) wallX += 1;

                BufferedImage texture = wallTextures.get(result.textureId);
                int texX = (int)(wallX * 64);

                if (wallHeight > 0) {
                    // Draw wall slice
                    int yStart = (SCREEN_HEIGHT - wallHeight) / 2;
                    for (int y = 0; y < wallHeight; y++) {
                        int texY = (int)((double)y / wallHeight * 64);
                        if (texY >= 0 && texY < 64) {
                            int color = texture.getRGB(texX, texY);
                            g2d.setColor(new Color(color));
                            g2d.drawLine(x, yStart + y, x, yStart + y);
                        }
                    }

                    // Add shadow for depth
                    if (result.side == 1) {
                        g2d.setColor(new Color(0, 0, 0, 50));
                        g2d.fillRect(x, yStart, 1, wallHeight);
                    }
                }
            }
        }
    }

    private RayResult castRay(double angle) {
        angle = (angle + 2 * Math.PI) % (2 * Math.PI);
        
        double rayDirX = Math.cos(angle);
        double rayDirY = Math.sin(angle);
        
        int mapX = (int)playerX;
        int mapY = (int)playerY;
        
        double deltaDistX = Math.abs(1 / rayDirX);
        double deltaDistY = Math.abs(1 / rayDirY);
        
        int stepX, stepY;
        double sideDistX, sideDistY;
        
        if (rayDirX < 0) {
            stepX = -1;
            sideDistX = (playerX - mapX) * deltaDistX;
        } else {
            stepX = 1;
            sideDistX = (mapX + 1.0 - playerX) * deltaDistX;
        }
        
        if (rayDirY < 0) {
            stepY = -1;
            sideDistY = (playerY - mapY) * deltaDistY;
        } else {
            stepY = 1;
            sideDistY = (mapY + 1.0 - playerY) * deltaDistY;
        }
        
        boolean hit = false;
        int side = 0;
        int textureId = 0;
        int steps = 0;
        
        while (!hit && steps < MAX_DEPTH) {
            if (sideDistX < sideDistY) {
                sideDistX += deltaDistX;
                mapX += stepX;
                side = 0;
            } else {
                sideDistY += deltaDistY;
                mapY += stepY;
                side = 1;
            }
            
            if (mapX < 0 || mapX >= map.length || mapY < 0 || mapY >= map[0].length) {
                break;
            }
            
            if (map[mapX][mapY] > 0) {
                hit = true;
                textureId = map[mapX][mapY] - 1;
            }
            steps++;
        }
        
        if (hit) {
            double perpWallDist;
            if (side == 0) {
                perpWallDist = (mapX - playerX + (1 - stepX) / 2.0) / rayDirX;
            } else {
                perpWallDist = (mapY - playerY + (1 - stepY) / 2.0) / rayDirY;
            }
            return new RayResult(perpWallDist, side, textureId);
        }
        
        return new RayResult(Double.MAX_VALUE, 0, 0);
    }

    private void renderEntities(Graphics2D g2d) {
        entities.sort((e1, e2) -> 
            Double.compare(e2.distanceToPlayer(playerX, playerY), e1.distanceToPlayer(playerX, playerY)));

        for (Entity entity : entities) {
            if (!entity.active) continue;
            if (!isEntityVisible(entity.x, entity.y)) continue;

            double entityDirX = entity.x - playerX;
            double entityDirY = entity.y - playerY;
            double entityAngle = Math.atan2(entityDirY, entityDirX) - playerAngle;
            
            // Normalize angle
            while (entityAngle < -Math.PI) entityAngle += 2 * Math.PI;
            while (entityAngle > Math.PI) entityAngle -= 2 * Math.PI;

            if (Math.abs(entityAngle) < HALF_FOV + 0.2) {
                double dist = Math.sqrt(entityDirX * entityDirX + entityDirY * entityDirY);
                dist *= Math.cos(entityAngle);

                if (dist > 0.5) {
                    int spriteHeight = Math.min((int)(SCREEN_HEIGHT / dist), SCREEN_HEIGHT * 2);
                    int spriteWidth = spriteHeight;

                    int spriteScreenX = (int)((SCREEN_WIDTH / 2.0) * (1 + entityAngle / HALF_FOV)) - spriteWidth / 2;
                    int spriteScreenY = (SCREEN_HEIGHT - spriteHeight) / 2;

                    if (spriteWidth > 0 && spriteHeight > 0) {
                        g2d.drawImage(entity.texture, spriteScreenX, spriteScreenY, spriteWidth, spriteHeight, null);
                    }
                }
            }
        }
    }

    private boolean isEntityVisible(double entityX, double entityY) {
        // Simple visibility check - more advanced version would use DDA
        double dx = entityX - playerX;
        double dy = entityY - playerY;
        double dist = Math.sqrt(dx * dx + dy * dy);
        
        int steps = (int)(dist * 10);
        for (int i = 1; i < steps; i++) {
            double t = (double)i / steps;
            double checkX = playerX + dx * t;
            double checkY = playerY + dy * t;
            
            int mapX = (int)checkX;
            int mapY = (int)checkY;
            
            if (mapX >= 0 && mapX < map.length && mapY >= 0 && mapY < map[0].length) {
                if (map[mapX][mapY] > 0) {
                    return false;
                }
            }
        }
        return true;
    }

    private void renderHUD(Graphics2D g2d) {
        // Health bar
        g2d.setColor(Color.DARK_GRAY);
        g2d.fillRect(10, 10, 204, 24);
        g2d.setColor(playerHealth < 30 ? Color.RED : Color.GREEN);
        g2d.fillRect(12, 12, 2 * playerHealth, 20);

        // Score
        g2d.setColor(Color.WHITE);
        g2d.setFont(new Font("Arial", Font.BOLD, 24));
        g2d.drawString("Score: " + playerScore, SCREEN_WIDTH - 150, 30);

        // Compass
        g2d.setColor(Color.WHITE);
        g2d.drawOval(SCREEN_WIDTH / 2 - 15, 15, 30, 30);
        double angleX = 12 * Math.cos(playerAngle);
        double angleY = 12 * Math.sin(playerAngle);
        g2d.setColor(Color.RED);
        g2d.drawLine(SCREEN_WIDTH / 2, 30, 
                    SCREEN_WIDTH / 2 + (int)angleX, 
                    30 + (int)angleY);
    }

    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        g.drawImage(buffer, 0, 0, null);
    }

    @Override
    public void keyPressed(KeyEvent e) {
        int keyCode = e.getKeyCode();
        if (keyCode < keys.length) {
            keys[keyCode] = true;
        }
        
        if (keyCode == KeyEvent.VK_SPACE) {
            for (Entity entity : entities) {
                if (entity.type.equals("enemy") && entity.active) {
                    double dist = entity.distanceToPlayer(playerX, playerY);
                    if (dist < 2.0) {
                        entity.active = false;
                        playerScore += 100;
                    }
                }
            }
        }
        
        if (keyCode == KeyEvent.VK_ESCAPE) {
            running = false;
            System.exit(0);
        }
    }

    @Override 
    public void keyReleased(KeyEvent e) {
        int keyCode = e.getKeyCode();
        if (keyCode < keys.length) {
            keys[keyCode] = false;
        }
    }

    @Override 
    public void keyTyped(KeyEvent e) {}

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            JFrame frame = new JFrame("Foxen3D ALPHABUILD");
            Foxen3D game = new Foxen3D();
            frame.add(game);
            frame.pack();
            frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
            frame.setLocationRelativeTo(null);
            frame.setResizable(false);
            frame.setVisible(true);

            new Thread(game).start();
        });
    }

    private static class RayResult {
        final double distance;
        final int side;
        final int textureId;

        RayResult(double distance, int side, int textureId) {
            this.distance = distance;
            this.side = side;
            this.textureId = textureId;
        }
    }

    private static class Entity {
        final double x, y;
        final String type;
        final BufferedImage texture;
        boolean active;

        Entity(double x, double y, String type, BufferedImage texture) {
            this.x = x;
            this.y = y;
            this.type = type;
            this.texture = texture;
            this.active = true;
        }

        void update(double playerX, double playerY) {
            // Simple update logic
        }

        double distanceToPlayer(double playerX, double playerY) {
            double dx = x - playerX;
            double dy = y - playerY;
            return Math.sqrt(dx * dx + dy * dy);
        }
    }
}
