import { useCallback, useState } from "react";
import { Alert } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { ApiError } from "./api";

export const errorMessage = (e: unknown, fallback = "Something went wrong.") =>
  e instanceof ApiError ? e.message : fallback;

/** Loads a list whenever the screen gains focus; `load` is also used for pull-to-refresh. */
export function useList<T>(fetcher: () => Promise<T[]>) {
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const load = useCallback(async () => {
    try { setItems(await fetcher()); setErr(null); }
    catch (e) { setErr(errorMessage(e, "Could not load.")); }
    finally { setLoading(false); }
  }, [fetcher]);
  useFocusEffect(useCallback(() => { load(); }, [load]));
  return { items, loading, err, load };
}

export function confirm(title: string, message: string, action: string, onConfirm: () => void) {
  Alert.alert(title, message, [
    { text: "Cancel", style: "cancel" },
    { text: action, style: "destructive", onPress: onConfirm },
  ]);
}
