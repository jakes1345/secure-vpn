# 🚀 Java Migration Guide - Step-by-Step

## Quick Start: Java Spring Boot Setup

### 1. Create Project Structure

```bash
mkdir secure-vpn-backend
cd secure-vpn-backend
```

### 2. Initialize Spring Boot Project

**Option A: Use Spring Initializr (Easiest)**
```bash
# Go to https://start.spring.io/
# Select:
# - Project: Maven
# - Language: Java
# - Spring Boot: 3.2.0
# - Dependencies:
#   - Spring Web
#   - Spring Data JPA
#   - PostgreSQL Driver
#   - Spring Security
#   - Redis
#   - Validation
# Download and extract
```

**Option B: Use CLI**
```bash
curl https://start.spring.io/starter.tgz \
  -d type=maven-project \
  -d language=java \
  -d bootVersion=3.2.0 \
  -d groupId=com.phazevpn \
  -d artifactId=secure-vpn-backend \
  -d dependencies=web,data-jpa,postgresql,security,data-redis,validation \
  | tar -xzf -
```

### 3. Project Structure

```
secure-vpn-backend/
├── pom.xml                          # Maven dependencies
├── src/main/java/com/phazevpn/
│   ├── SecureVpnApplication.java   # Main class
│   ├── config/
│   │   ├── SecurityConfig.java     # Security configuration
│   │   ├── DatabaseConfig.java     # Database configuration
│   │   └── RedisConfig.java        # Redis configuration
│   ├── controller/
│   │   ├── AuthController.java     # Login/logout
│   │   ├── UserController.java     # User CRUD
│   │   ├── PaymentController.java  # Stripe payments
│   │   └── VpnConfigController.java # Config generation
│   ├── service/
│   │   ├── UserService.java
│   │   ├── PaymentService.java
│   │   └── VpnConfigService.java
│   ├── repository/
│   │   ├── UserRepository.java
│   │   ├── SubscriptionRepository.java
│   │   └── PaymentRepository.java
│   └── model/
│       ├── User.java
│       ├── Subscription.java
│       └── Payment.java
└── src/main/resources/
    ├── application.yml              # Configuration
    └── db/migration/                 # Database migrations
```

---

## 📦 Dependencies (pom.xml)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>
    
    <groupId>com.phazevpn</groupId>
    <artifactId>secure-vpn-backend</artifactId>
    <version>1.0.0</version>
    <name>SecureVPN Backend</name>
    
    <properties>
        <java.version>17</java.version>
    </properties>
    
    <dependencies>
        <!-- Spring Boot Starters -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>
        
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-redis</artifactId>
        </dependency>
        
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        
        <!-- Database -->
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <scope>runtime</scope>
        </dependency>
        
        <!-- Database Migrations -->
        <dependency>
            <groupId>org.flywaydb</groupId>
            <artifactId>flyway-core</artifactId>
        </dependency>
        
        <!-- Stripe -->
        <dependency>
            <groupId>com.stripe</groupId>
            <artifactId>stripe-java</artifactId>
            <version>24.0.0</version>
        </dependency>
        
        <!-- JSON Processing -->
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
        </dependency>
        
        <!-- JWT -->
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-api</artifactId>
            <version>0.12.3</version>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-impl</artifactId>
            <version>0.12.3</version>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-jackson</artifactId>
            <version>0.12.3</version>
            <scope>runtime</scope>
        </dependency>
        
        <!-- Testing -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        
        <dependency>
            <groupId>org.springframework.security</groupId>
            <artifactId>spring-security-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

---

## ⚙️ Configuration (application.yml)

```yaml
spring:
  application:
    name: secure-vpn-backend
  
  # Database Configuration
  datasource:
    url: jdbc:postgresql://localhost:5432/phazevpn
    username: ${DB_USERNAME:phazevpn}
    password: ${DB_PASSWORD:changeme}
    driver-class-name: org.postgresql.Driver
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
      connection-timeout: 30000
      idle-timeout: 600000
      max-lifetime: 1800000
  
  # JPA Configuration
  jpa:
    hibernate:
      ddl-auto: validate  # Use Flyway for migrations
    show-sql: false
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
        format_sql: true
        use_sql_comments: true
  
  # Flyway (Database Migrations)
  flyway:
    enabled: true
    locations: classpath:db/migration
    baseline-on-migrate: true
  
  # Redis Configuration
  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}
      password: ${REDIS_PASSWORD:}
      timeout: 2000ms
      lettuce:
        pool:
          max-active: 10
          max-idle: 5
          min-idle: 2
  
  # Security
  security:
    user:
      name: admin
      password: ${ADMIN_PASSWORD:changeme}

# Server Configuration
server:
  port: ${PORT:8080}
  compression:
    enabled: true
    mime-types: application/json,application/xml,text/html,text/xml,text/plain
  error:
    include-message: always
    include-stacktrace: on_param

# Stripe Configuration
stripe:
  api-key: ${STRIPE_SECRET_KEY:}
  webhook-secret: ${STRIPE_WEBHOOK_SECRET:}
  public-key: ${STRIPE_PUBLIC_KEY:}

# JWT Configuration
jwt:
  secret: ${JWT_SECRET:changeme}
  expiration: 86400000  # 24 hours

# Logging
logging:
  level:
    root: INFO
    com.phazevpn: DEBUG
    org.springframework.security: DEBUG
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss} - %msg%n"
```

---

## 🗄️ Database Models

### User.java

```java
package com.phazevpn.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;
import java.util.Set;

@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(unique = true, nullable = false, length = 50)
    @NotBlank
    @Size(min = 3, max = 50)
    private String username;
    
    @Column(nullable = false)
    @NotBlank
    private String passwordHash;
    
    @Email
    @Column(unique = true)
    private String email;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Role role = Role.USER;
    
    @Column(nullable = false)
    private boolean enabled = true;
    
    @Column(nullable = false)
    private LocalDateTime createdAt = LocalDateTime.now();
    
    @Column(nullable = false)
    private LocalDateTime updatedAt = LocalDateTime.now();
    
    @OneToOne(mappedBy = "user", cascade = CascadeType.ALL)
    private Subscription subscription;
    
    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL)
    private Set<Payment> payments;
    
    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    
    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }
    
    public String getPasswordHash() { return passwordHash; }
    public void setPasswordHash(String passwordHash) { this.passwordHash = passwordHash; }
    
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    
    public Role getRole() { return role; }
    public void setRole(Role role) { this.role = role; }
    
    public boolean isEnabled() { return enabled; }
    public void setEnabled(boolean enabled) { this.enabled = enabled; }
    
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
    
    public Subscription getSubscription() { return subscription; }
    public void setSubscription(Subscription subscription) { this.subscription = subscription; }
    
    public Set<Payment> getPayments() { return payments; }
    public void setPayments(Set<Payment> payments) { this.payments = payments; }
    
    @PreUpdate
    public void preUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
}

enum Role {
    USER, PREMIUM, PRO, MODERATOR, ADMIN
}
```

### Subscription.java

```java
package com.phazevpn.model;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "subscriptions")
public class Subscription {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @OneToOne
    @JoinColumn(name = "user_id", nullable = false, unique = true)
    private User user;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private SubscriptionTier tier = SubscriptionTier.FREE;
    
    @Column(nullable = false)
    private BigDecimal price = BigDecimal.ZERO;
    
    @Column(nullable = false)
    private LocalDateTime startDate = LocalDateTime.now();
    
    @Column(nullable = false)
    private LocalDateTime endDate;
    
    @Column(nullable = false)
    private boolean active = true;
    
    @Column(unique = true)
    private String stripeSubscriptionId;
    
    @Column(unique = true)
    private String stripeCustomerId;
    
    // Getters and Setters
    // ... (similar to User)
}

enum SubscriptionTier {
    FREE, PREMIUM, PRO
}
```

---

## 🔐 Security Configuration

### SecurityConfig.java

```java
package com.phazevpn.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;
import java.util.List;

@Configuration
@EnableWebSecurity
public class SecurityConfig {
    
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())  // Disable for API (use JWT instead)
            .cors(cors -> cors.configurationSource(corsConfigurationSource()))
            .sessionManagement(session -> 
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**").permitAll()
                .requestMatchers("/api/public/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .requestMatchers("/api/**").authenticated()
                .anyRequest().permitAll()
            );
        
        return http.build();
    }
    
    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        configuration.setAllowedOrigins(List.of("http://localhost:3000", "https://phazevpn.com"));
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS"));
        configuration.setAllowedHeaders(List.of("*"));
        configuration.setAllowCredentials(true);
        
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
    
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
```

---

## 🎯 REST Controllers

### AuthController.java

```java
package com.phazevpn.controller;

import com.phazevpn.model.User;
import com.phazevpn.service.AuthService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
    
    @Autowired
    private AuthService authService;
    
    @PostMapping("/login")
    public ResponseEntity<?> login(@Valid @RequestBody LoginRequest request) {
        String token = authService.login(request.getUsername(), request.getPassword());
        return ResponseEntity.ok(Map.of("token", token));
    }
    
    @PostMapping("/logout")
    public ResponseEntity<?> logout(@RequestHeader("Authorization") String token) {
        authService.logout(token);
        return ResponseEntity.ok(Map.of("message", "Logged out"));
    }
    
    @PostMapping("/register")
    public ResponseEntity<?> register(@Valid @RequestBody RegisterRequest request) {
        User user = authService.register(request);
        return ResponseEntity.ok(user);
    }
}
```

### UserController.java

```java
package com.phazevpn.controller;

import com.phazevpn.model.User;
import com.phazevpn.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/users")
public class UserController {
    
    @Autowired
    private UserService userService;
    
    @GetMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<List<User>> getAllUsers() {
        return ResponseEntity.ok(userService.getAllUsers());
    }
    
    @GetMapping("/{id}")
    public ResponseEntity<User> getUser(@PathVariable Long id) {
        return ResponseEntity.ok(userService.getUserById(id));
    }
    
    @PutMapping("/{id}")
    public ResponseEntity<User> updateUser(@PathVariable Long id, @RequestBody User user) {
        return ResponseEntity.ok(userService.updateUser(id, user));
    }
    
    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<?> deleteUser(@PathVariable Long id) {
        userService.deleteUser(id);
        return ResponseEntity.ok().build();
    }
}
```

---

## 🗄️ Database Migration (Flyway)

### V1__Create_users_table.sql

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    role VARCHAR(20) NOT NULL DEFAULT 'USER',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

### V2__Create_subscriptions_table.sql

```sql
CREATE TABLE subscriptions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tier VARCHAR(20) NOT NULL DEFAULT 'FREE',
    price DECIMAL(10,2) NOT NULL DEFAULT 0,
    start_date TIMESTAMP NOT NULL DEFAULT NOW(),
    end_date TIMESTAMP NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255) UNIQUE
);

CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_active ON subscriptions(active);
```

---

## 🚀 Running the Application

```bash
# Build
mvn clean package

# Run
java -jar target/secure-vpn-backend-1.0.0.jar

# Or with Maven
mvn spring-boot:run
```

---

## 📝 Next Steps

1. **Set up PostgreSQL database**
2. **Configure Redis**
3. **Set environment variables**
4. **Run migrations**
5. **Test endpoints**

See `TECHNICAL-DEEP-DIVE.md` for full architecture details.

