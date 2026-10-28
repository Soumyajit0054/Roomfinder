import React, { useState } from "react";
import { Modal, Pressable, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "./auth";
import Icon, { IconName } from "./Icon";
import { colors, shadow } from "./ui";

export type MenuItem = { name: string; title: string; icon: IconName };

/** Hamburger button for the header's top-right corner; opens a dropdown of the role's screens. */
export default function MenuButton({ items, active, onNavigate }: {
  items: MenuItem[]; active: string; onNavigate: (name: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const { user, signOut } = useAuth();
  const insets = useSafeAreaInsets();

  const go = (name: string) => { setOpen(false); if (name !== active) onNavigate(name); };

  return (
    <>
      <Pressable onPress={() => setOpen(true)} accessibilityLabel="Open menu" accessibilityRole="button" hitSlop={10}
        style={{ paddingHorizontal: 14, paddingVertical: 8 }}>
        <Icon name="list" size={26} color="#fff" />
      </Pressable>

      <Modal visible={open} transparent animationType="fade" onRequestClose={() => setOpen(false)} statusBarTranslucent>
        <Pressable style={{ flex: 1, backgroundColor: "rgba(0,0,0,0.35)" }} onPress={() => setOpen(false)}>
          <View style={[{ position: "absolute", top: insets.top + 56, right: 12, width: 250, backgroundColor: "#fff", borderRadius: 16, paddingVertical: 8, borderWidth: 1, borderColor: colors.border }, shadow]}>
            <View style={{ paddingHorizontal: 16, paddingVertical: 10, borderBottomWidth: 1, borderColor: colors.border }}>
              <Text style={{ fontWeight: "800", fontSize: 15, color: colors.text }} numberOfLines={1}>{user?.name}</Text>
              <Text style={{ color: colors.muted, fontSize: 12, textTransform: "capitalize" }}>{user?.role}</Text>
            </View>

            {items.map((it) => {
              const on = it.name === active;
              return (
                <Pressable key={it.name} onPress={() => go(it.name)} accessibilityRole="menuitem"
                  style={({ pressed }) => ({ flexDirection: "row", alignItems: "center", gap: 12, paddingHorizontal: 16, paddingVertical: 13, backgroundColor: on ? colors.tintBlue : pressed ? "#f3f5f8" : "transparent" })}>
                  <Icon name={it.icon} size={18} color={on ? colors.primary : colors.muted} />
                  <Text style={{ fontSize: 16, fontWeight: on ? "800" : "500", color: on ? colors.primary : colors.text }}>{it.title}</Text>
                </Pressable>
              );
            })}

            <View style={{ borderTopWidth: 1, borderColor: colors.border, marginTop: 4 }}>
              <Pressable onPress={() => { setOpen(false); signOut(); }} accessibilityRole="menuitem"
                style={({ pressed }) => ({ flexDirection: "row", alignItems: "center", gap: 12, paddingHorizontal: 16, paddingVertical: 13, backgroundColor: pressed ? "#f3f5f8" : "transparent" })}>
                <Icon name="box-arrow-right" size={18} color={colors.danger} />
                <Text style={{ fontSize: 16, color: colors.danger, fontWeight: "600" }}>Log out</Text>
              </Pressable>
            </View>
          </View>
        </Pressable>
      </Modal>
    </>
  );
}
