import React, { useState } from "react";
import {
  ActivityIndicator, Image, Pressable, StyleSheet, Text, TextInput, TextInputProps, View, ViewStyle,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Property } from "./api";
import Icon, { IconName } from "./Icon";

// Design tokens copied from the web app's static/css/style.css (:root)
export const colors = {
  primary: "#1f4e79",
  primaryDark: "#163a5c",
  accent: "#c9a227",
  bg: "#f5f7fa",
  card: "#ffffff",
  text: "#1f2933",
  muted: "#6b7280",
  border: "#e1e5ea",
  success: "#2e7d32",
  danger: "#c62828",
  warning: "#b7791f",
  tintBlue: "#e8f0f8",
  tintRed: "#fdecec",
  tintGold: "#fdf3e3",
  tintGreen: "#e8f5e9",
};

export const shadow: ViewStyle = {
  shadowColor: "#000", shadowOpacity: 0.07, shadowRadius: 10, shadowOffset: { width: 0, height: 4 }, elevation: 2,
};

// ---------------------------------------------------------------- header

export const GradientBackground = () => (
  <LinearGradient colors={[colors.primary, colors.primaryDark]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} />
);

export const Brand = ({ size = 20, color = "#fff" }: { size?: number; color?: string }) => (
  <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
    <Icon name="house-heart" size={size + 4} color={color} />
    <Text style={{ color, fontSize: size, fontWeight: "800", letterSpacing: -0.4 }}>RoomFinder</Text>
  </View>
);

/** Shared react-navigation header options: navy gradient bar with white text. */
export const headerOptions = {
  headerBackground: GradientBackground,
  headerTintColor: "#fff",
  headerTitleStyle: { color: "#fff", fontWeight: "700" as const },
  headerShadowVisible: false,
};

// ---------------------------------------------------------------- inputs & buttons

export function Button({ title, onPress, loading, variant = "primary", disabled, icon }: {
  title: string; onPress: () => void; loading?: boolean; variant?: "primary" | "outline"; disabled?: boolean; icon?: IconName;
}) {
  const outline = variant === "outline";
  const fg = outline ? colors.primary : "#fff";
  return (
    <Pressable
      onPress={onPress}
      disabled={loading || disabled}
      accessibilityRole="button"
      style={({ pressed }) => [s.btn, outline && s.btnOutline, (pressed || disabled) && { opacity: 0.75 }]}
    >
      {loading ? <ActivityIndicator color={fg} /> : (
        <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
          {icon && <Icon name={icon} size={17} color={fg} />}
          <Text style={[s.btnText, { color: fg }]}>{title}</Text>
        </View>
      )}
    </Pressable>
  );
}

export function Field(props: TextInputProps & { label: string; icon?: IconName }) {
  const { label, icon, style, secureTextEntry, ...rest } = props;
  const [hidden, setHidden] = useState(!!secureTextEntry);
  return (
    <View style={{ marginBottom: 14 }}>
      <Text style={s.label}>{label}</Text>
      <View style={[s.inputWrap, rest.multiline && { alignItems: "flex-start" }]}>
        {icon && <View style={s.inputIcon}><Icon name={icon} size={16} color={colors.muted} /></View>}
        <TextInput
          placeholderTextColor={colors.muted}
          secureTextEntry={hidden}
          style={[s.input, style]}
          {...rest}
        />
        {secureTextEntry && (
          <Pressable onPress={() => setHidden((h) => !h)} style={s.inputIcon} accessibilityLabel={hidden ? "Show password" : "Hide password"}>
            <Icon name={hidden ? "eye" : "eye-slash"} size={17} color={colors.muted} />
          </Pressable>
        )}
      </View>
    </View>
  );
}

export const SearchInput = (props: TextInputProps) => (
  <View style={[s.inputWrap, { backgroundColor: "#fff" }]}>
    <View style={s.inputIcon}><Icon name="search" size={16} color={colors.muted} /></View>
    <TextInput placeholderTextColor={colors.muted} style={s.input} {...props} />
  </View>
);

export const ErrorText = ({ children }: { children?: string | null }) =>
  children ? (
    <View style={s.alert}>
      <Icon name="exclamation-circle" size={16} color={colors.danger} />
      <Text style={{ color: colors.danger, flex: 1 }}>{children}</Text>
    </View>
  ) : null;

// ---------------------------------------------------------------- layout bits

export const Eyebrow = ({ children }: { children: string }) => (
  <Text style={{ color: colors.primary, fontSize: 12, fontWeight: "800", letterSpacing: 1.5, textTransform: "uppercase" }}>{children}</Text>
);

export const SectionHeader = ({ eyebrow, title, subtitle, action, onAction }: {
  eyebrow?: string; title: string; subtitle?: string; action?: string; onAction?: () => void;
}) => (
  <View style={{ flexDirection: "row", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 12 }}>
    <View style={{ flex: 1 }}>
      {eyebrow && <Eyebrow>{eyebrow}</Eyebrow>}
      <Text style={{ fontSize: 22, fontWeight: "800", color: colors.text }}>{title}</Text>
      {subtitle && <Text style={{ color: colors.muted, marginTop: 2 }}>{subtitle}</Text>}
    </View>
    {action && (
      <Pressable onPress={onAction} style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
        <Text style={{ fontWeight: "700", color: colors.text }}>{action}</Text>
        <Icon name="arrow-right" size={14} color={colors.text} />
      </Pressable>
    )}
  </View>
);

export const Empty = ({ text, icon = "house-x" }: { text: string; icon?: IconName }) => (
  <View style={{ padding: 40, alignItems: "center" }}>
    <View style={s.emptyIcon}><Icon name={icon} size={30} color={colors.primary} /></View>
    <Text style={{ color: colors.muted, textAlign: "center" }}>{text}</Text>
  </View>
);

export const Center = ({ children }: { children?: React.ReactNode }) => (
  <View style={{ flex: 1, alignItems: "center", justifyContent: "center", padding: 24 }}>{children}</View>
);

export const Row = ({ children, style }: { children: React.ReactNode; style?: object }) => (
  <View style={[s.panel, style]}>{children}</View>
);

export const Pill = ({ label, color = colors.primary, bg = colors.tintBlue, icon }: { label: string; color?: string; bg?: string; icon?: IconName }) => (
  <View style={{ flexDirection: "row", alignItems: "center", gap: 5, backgroundColor: bg, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 999, alignSelf: "flex-start" }}>
    {icon && <Icon name={icon} size={12} color={color} />}
    <Text style={{ color, fontWeight: "700", fontSize: 12, textTransform: "capitalize" }}>{label}</Text>
  </View>
);

const BADGE = {
  pending: { color: colors.warning, bg: colors.tintGold, icon: "clock" },
  accepted: { color: colors.success, bg: colors.tintGreen, icon: "check-circle" },
  rejected: { color: colors.danger, bg: colors.tintRed, icon: "x-circle" },
} as const;

export const StatusBadge = ({ status }: { status: keyof typeof BADGE }) => (
  <Pill label={status} color={BADGE[status].color} bg={BADGE[status].bg} icon={BADGE[status].icon} />
);

export const IconTile = ({ name, color = colors.primary, bg = colors.tintBlue, size = 50 }: { name: IconName; color?: string; bg?: string; size?: number }) => (
  <View style={{ width: size, height: size, borderRadius: 14, backgroundColor: bg, alignItems: "center", justifyContent: "center" }}>
    <Icon name={name} size={size * 0.46} color={color} />
  </View>
);

export const StatCard = ({ label, value, icon = "house", tone = "blue" }: {
  label: string; value: number | string; icon?: IconName; tone?: "blue" | "red" | "gold" | "green";
}) => {
  const t = { blue: [colors.primary, colors.tintBlue], red: [colors.danger, colors.tintRed], gold: [colors.warning, colors.tintGold], green: [colors.success, colors.tintGreen] }[tone];
  return (
    <View style={[s.panel, { flexBasis: "100%", flexDirection: "row", alignItems: "center", gap: 14, marginBottom: 0, padding: 16 }]}>
      <IconTile name={icon} color={t[0]} bg={t[1]} />
      <View>
        <Text style={{ color: colors.muted, fontSize: 13 }}>{label}</Text>
        <Text style={{ fontSize: 24, fontWeight: "800", color: colors.text }}>{value}</Text>
      </View>
    </View>
  );
};

// ---------------------------------------------------------------- property card

export function PropertyCard({ item, onPress }: { item: Property; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={[s.card, shadow]} accessibilityRole="button">
      <View>
        {item.image
          ? <Image source={{ uri: item.image }} style={s.cardImg} />
          : <View style={[s.cardImg, { alignItems: "center", justifyContent: "center", backgroundColor: colors.tintBlue }]}><Icon name="house" size={44} color={colors.primary} /></View>}
        <View style={{ position: "absolute", left: 10, top: 10 }}>
          <Pill label={item.available ? "Available" : "Taken"} color="#fff" bg={item.available ? colors.success : colors.muted} />
        </View>
        <View style={{ position: "absolute", right: 10, top: 10 }}>
          <Pill label={item.room_type} color={colors.primary} bg="#ffffffee" />
        </View>
      </View>
      <View style={{ padding: 14 }}>
        <Text style={s.cardTitle} numberOfLines={1}>{item.title}</Text>
        <View style={s.metaRow}>
          <Icon name="geo-alt" size={14} color={colors.primary} />
          <Text style={{ color: colors.muted, flex: 1 }} numberOfLines={1}>{item.location}</Text>
        </View>
        <View style={[s.metaRow, { gap: 16, marginTop: 8 }]}>
          {!!item.furnished && <View style={s.metaRow}><Icon name="box-seam" size={14} color={colors.muted} /><Text style={s.metaText}>{item.furnished === "Yes" ? "Furnished" : "Unfurnished"}</Text></View>}
          {!!item.food_available && <View style={s.metaRow}><Icon name="cup-hot" size={14} color={colors.muted} /><Text style={s.metaText}>Food {item.food_available}</Text></View>}
        </View>
        <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderColor: colors.border }}>
          <Text style={s.rent}>₹{item.rent.toLocaleString()}<Text style={{ fontSize: 13, color: colors.muted, fontWeight: "500" }}> / month</Text></Text>
          <View style={s.go}><Icon name="arrow-right" size={15} color="#fff" /></View>
        </View>
      </View>
    </Pressable>
  );
}

const s = StyleSheet.create({
  btn: { backgroundColor: colors.primary, borderRadius: 10, minHeight: 50, alignItems: "center", justifyContent: "center", paddingHorizontal: 18, borderWidth: 1.5, borderColor: colors.primary },
  btnOutline: { backgroundColor: "#fff" },
  btnText: { fontWeight: "700", fontSize: 16 },
  label: { fontWeight: "700", marginBottom: 6, color: colors.text, fontSize: 13 },
  inputWrap: { flexDirection: "row", alignItems: "center", borderWidth: 1, borderColor: colors.border, borderRadius: 10, backgroundColor: "#fff", minHeight: 50, overflow: "hidden" },
  inputIcon: { paddingHorizontal: 13, height: 50, justifyContent: "center", backgroundColor: "transparent" },
  input: { flex: 1, fontSize: 16, color: colors.text, paddingRight: 12, paddingLeft: 4, minHeight: 50 },
  alert: { flexDirection: "row", alignItems: "center", gap: 8, backgroundColor: colors.tintRed, padding: 12, borderRadius: 10, marginBottom: 12 },
  emptyIcon: { width: 76, height: 76, borderRadius: 20, backgroundColor: colors.tintBlue, alignItems: "center", justifyContent: "center", marginBottom: 14 },
  panel: { backgroundColor: colors.card, borderRadius: 14, padding: 14, marginBottom: 12, borderWidth: 1, borderColor: colors.border },
  card: { backgroundColor: colors.card, borderRadius: 16, marginBottom: 16, overflow: "hidden", borderWidth: 1, borderColor: colors.border },
  cardImg: { width: "100%", height: 180, backgroundColor: "#e9ecef" },
  cardTitle: { fontSize: 18, fontWeight: "800", color: colors.text, marginBottom: 6 },
  metaRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  metaText: { color: colors.muted, fontSize: 13 },
  rent: { fontWeight: "800", color: colors.primary, fontSize: 20 },
  go: { width: 34, height: 34, borderRadius: 17, backgroundColor: colors.primary, alignItems: "center", justifyContent: "center" },
});
